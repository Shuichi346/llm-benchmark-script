"""
モデル生成・事前チェックの統合インターフェース

LLM_BACKEND の値に応じて Ollama / LM Studio の処理を振り分ける。
"""

import sys

from deepeval.models import DeepEvalBaseLLM

from models.ollama_model import (
    create_ollama_model,
    preflight_check_ollama,
    get_ollama_display_info,
)
from models.lmstudio_model import (
    create_lmstudio_model,
    preflight_check_lmstudio,
    get_lmstudio_display_info,
)


def create_model(backend: str, model_name: str) -> DeepEvalBaseLLM:
    """バックエンドに応じたモデルインスタンスを生成する"""
    if backend == "ollama":
        return create_ollama_model(model_name)
    if backend == "lmstudio":
        return create_lmstudio_model(model_name)
    raise ValueError(f"未対応のバックエンド: {backend}")


def preflight_check(backend: str, model_names: list[str]) -> list[str]:
    """バックエンドに応じた事前チェックを実行し、有効なモデル一覧を返す"""
    print("\n--- 事前チェック ---")

    if backend == "ollama":
        valid_models = preflight_check_ollama(model_names)
    elif backend == "lmstudio":
        valid_models = preflight_check_lmstudio(model_names)
    else:
        raise ValueError(f"未対応のバックエンド: {backend}")

    if not valid_models:
        print("\n[エラー] 使用可能なモデルがありません。")
        sys.exit(1)

    skipped = len(model_names) - len(valid_models)
    if skipped > 0:
        print(f"\n  [注意] {skipped} 個のモデルをスキップします。")

    print()
    return valid_models


def get_backend_display_info(backend: str) -> dict[str, str]:
    """バックエンドの表示用情報を取得する"""
    if backend == "ollama":
        return get_ollama_display_info()
    if backend == "lmstudio":
        return get_lmstudio_display_info()
    return {"name": backend, "url": "N/A"}
