"""
Ollama バックエンド用のモデル生成・事前チェック
"""

import inspect
import json as json_mod
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from deepeval.models import OllamaModel


def _get_base_url() -> str:
    """Ollama のベース URL を取得する"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
    if not base_url:
        base_url = "http://localhost:11434"
    return base_url


def _check_connection(base_url: str) -> bool:
    """Ollama サーバーへの接続を確認する"""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def _check_model_available(
    base_url: str, model_name: str
) -> tuple[bool, str]:
    """Ollama にモデルが存在し、ロード可能かテスト生成で確認する"""
    try:
        payload = json_mod.dumps({
            "model": model_name,
            "prompt": "Hi",
            "stream": False,
            "options": {"num_predict": 1},
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
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


def create_ollama_model(model_name: str) -> OllamaModel:
    """OllamaModel インスタンスを生成する"""
    base_url = _get_base_url()

    try:
        signature = inspect.signature(OllamaModel)
        parameters = signature.parameters
    except (TypeError, ValueError):
        return OllamaModel(
            model=model_name,
            base_url=base_url,
            temperature=0.0,
        )

    kwargs: dict[str, Any] = {}

    if "model" in parameters:
        kwargs["model"] = model_name
    elif "model_name" in parameters:
        kwargs["model_name"] = model_name
    else:
        kwargs["model"] = model_name

    if "base_url" in parameters:
        kwargs["base_url"] = base_url
    elif "host" in parameters:
        kwargs["host"] = base_url

    if "temperature" in parameters:
        kwargs["temperature"] = 0.0

    return OllamaModel(**kwargs)


def preflight_check_ollama(model_names: list[str]) -> list[str]:
    """Ollama 接続とモデルの動作を事前確認し、有効なモデル一覧を返す"""
    base_url = _get_base_url()

    if not _check_connection(base_url):
        print(f"[エラー] Ollama ({base_url}) に接続できません。")
        print("  → Ollama が起動しているか確認してください: ollama serve")
        sys.exit(1)

    print(f"  Ollama 接続OK: {base_url}")

    valid_models: list[str] = []

    for model_name in model_names:
        print(f"  モデル確認中: {model_name} ...", end=" ", flush=True)
        ok, error_msg = _check_model_available(base_url, model_name)

        if ok:
            print("OK")
            valid_models.append(model_name)
        else:
            print("NG")
            print(f"    → {error_msg}")
            print(f"    → このモデルはスキップします。")

    return valid_models


def get_ollama_display_info() -> dict[str, str]:
    """Ollama の表示用情報を返す"""
    return {
        "name": "Ollama",
        "url": _get_base_url(),
    }
