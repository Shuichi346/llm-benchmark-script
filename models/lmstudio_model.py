"""
LM Studio バックエンド用のカスタムモデルクラスと事前チェック

LM Studio の OpenAI 互換 API を使い、deepeval の DeepEvalBaseLLM として動作する。
応答テキストから正解パターンを抽出するクリーニング処理を含む。
"""

import asyncio
import json as json_mod
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

from openai import OpenAI
from deepeval.models import DeepEvalBaseLLM


def _extract_answer(text: str) -> str:
    """LLM の応答テキストからベンチマーク正解値を抽出する

    deepeval のベンチマークは exact match で採点するため、
    応答から正解部分だけを取り出す必要がある。
    対応する形式:
      - MMLU: A, B, C, D（単一アルファベット）
      - TruthfulQA MC1: 1, 2, 3 ... （単一数字）
      - TruthfulQA MC2: [1, 3, 4]（数値リスト）
      - GSM8K: 整数または小数の数値
    """
    if not text:
        return ""

    # 特殊トークンと前後の空白を除去
    cleaned = re.sub(
        r"<\|[a-z_]+\|>", "", text, flags=re.IGNORECASE
    ).strip()

    if not cleaned:
        return ""

    # TruthfulQA MC2 形式: [1, 3, 4] のようなリスト
    list_match = re.search(r"\[[\d\s,]+\]", cleaned)
    if list_match:
        return list_match.group(0)

    # MMLU 形式: 先頭付近の A/B/C/D 単独文字を探す
    # 「A」「A.」「A)」「(A)」「Answer: A」のようなパターンに対応
    letter_match = re.match(r"^[^A-Da-d]*?\b([A-Da-d])\b", cleaned)
    if letter_match:
        candidate = letter_match.group(1).upper()
        # 応答が短い場合（20文字以内）はこの文字を信頼する
        if len(cleaned) <= 20:
            return candidate
        # 応答が長い場合でも、先頭に近い文字であれば採用
        if letter_match.start(1) < 15:
            return candidate

    # TruthfulQA MC1 / GSM8K 形式: 数値を抽出
    # 応答の先頭付近にある数値を優先的に取得する
    number_match = re.match(r"^[^\d-]*?(-?[\d,]+\.?\d*)", cleaned)
    if number_match:
        num_str = number_match.group(1).replace(",", "")
        return num_str

    # どのパターンにも該当しない場合はクリーニング済みテキストを返す
    return cleaned


def _get_base_url() -> str:
    """LM Studio のベース URL を取得する"""
    base_url = os.getenv(
        "LMSTUDIO_BASE_URL", "http://localhost:1234/v1"
    ).strip()
    if not base_url:
        base_url = "http://localhost:1234/v1"
    return base_url


def _get_api_key() -> str:
    """LM Studio の API キーを取得する（通常はダミーで良い）"""
    return (
        os.getenv("LMSTUDIO_API_KEY", "lm-studio").strip() or "lm-studio"
    )


class LMStudioModel(DeepEvalBaseLLM):
    """LM Studio の OpenAI 互換 API を利用する deepeval カスタムモデル"""

    def __init__(self, model_name: str, base_url: str, api_key: str):
        self._model_name = model_name
        self._base_url = base_url
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def load_model(self) -> OpenAI:
        """モデルオブジェクト（OpenAI クライアント）を返す"""
        return self._client

    def generate(self, prompt: str) -> str:
        """プロンプトを送信し、正解値を抽出して返す"""
        client = self.load_model()
        response = client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw_content = response.choices[0].message.content or ""
        return _extract_answer(raw_content)

    async def a_generate(self, prompt: str) -> str:
        """非同期版の生成メソッド（スレッドプールに委譲）"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate, prompt)

    def get_model_name(self) -> str:
        """モデル名を返す"""
        return self._model_name


def create_lmstudio_model(model_name: str) -> LMStudioModel:
    """LMStudioModel インスタンスを生成する"""
    base_url = _get_base_url()
    api_key = _get_api_key()
    return LMStudioModel(
        model_name=model_name, base_url=base_url, api_key=api_key
    )


def _check_connection(base_url: str) -> bool:
    """LM Studio サーバーへの接続を確認する"""
    try:
        models_url = f"{base_url}/models"
        req = urllib.request.Request(models_url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def _check_model_available(
    base_url: str, model_name: str, api_key: str
) -> tuple[bool, str]:
    """LM Studio でモデルが応答可能かテスト生成で確認する"""
    try:
        payload = json_mod.dumps({
            "model": model_name,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
            "temperature": 0.0,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            if resp.status == 200:
                return True, ""
            return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return False, f"HTTP {exc.code}: {body}"
    except Exception as exc:
        return False, str(exc)


def preflight_check_lmstudio(model_names: list[str]) -> list[str]:
    """LM Studio 接続とモデルの動作を事前確認し、有効なモデル一覧を返す"""
    base_url = _get_base_url()
    api_key = _get_api_key()

    if not _check_connection(base_url):
        print(f"[エラー] LM Studio ({base_url}) に接続できません。")
        print("  → LM Studio を起動し、ローカルサーバーを開始してください。")
        print(
            "  → LM Studio の「Developer」タブで Server を Start してください。"
        )
        sys.exit(1)

    print(f"  LM Studio 接続OK: {base_url}")

    valid_models: list[str] = []

    for model_name in model_names:
        print(f"  モデル確認中: {model_name} ...", end=" ", flush=True)
        ok, error_msg = _check_model_available(
            base_url, model_name, api_key
        )

        if ok:
            print("OK")
            valid_models.append(model_name)
        else:
            print("NG")
            print(f"    → {error_msg}")
            print(f"    → このモデルはスキップします。")
            print(
                f"    → LM Studio でこのモデルがロードされているか"
                f"確認してください。"
            )

    return valid_models


def get_lmstudio_display_info() -> dict[str, str]:
    """LM Studio の表示用情報を返す"""
    return {
        "name": "LM Studio (OpenAI互換API)",
        "url": _get_base_url(),
    }
