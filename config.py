"""
環境変数の読み込み・バリデーション

.env ファイルから設定値を取得し、型変換・範囲チェック・正規化を行う。
"""

import os
from typing import Any

from dotenv import load_dotenv


SUPPORTED_BENCHMARKS: dict[str, str] = {
    "mmlu": "MMLU",
    "truthfulqa": "TruthfulQA",
    "gsm8k": "GSM8K",
}

SUPPORTED_BACKENDS = {"ollama", "lmstudio"}

TRUE_VALUES = {"true", "1", "yes", "y", "on"}
FALSE_VALUES = {"false", "0", "no", "n", "off"}


def load_env() -> None:
    """.env ファイルを読み込む"""
    load_dotenv(override=True)


def get_env_list(key: str, default: str = "") -> list[str]:
    """環境変数からカンマ区切りのリストを取得する"""
    value = os.getenv(key, default).strip()
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def get_env_int(
    key: str,
    default: int = 0,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """環境変数から整数値を取得する"""
    raw_value = os.getenv(key)

    if raw_value is None or raw_value.strip() == "":
        value = default
    else:
        try:
            value = int(raw_value.strip())
        except ValueError as exc:
            raise ValueError(
                f"{key} は整数で指定してください。現在の値: {raw_value}"
            ) from exc

    if minimum is not None and value < minimum:
        raise ValueError(
            f"{key} は {minimum} 以上で指定してください。現在の値: {value}"
        )

    if maximum is not None and value > maximum:
        raise ValueError(
            f"{key} は {maximum} 以下で指定してください。現在の値: {value}"
        )

    return value


def get_env_bool(key: str, default: bool = False) -> bool:
    """環境変数から真偽値を取得する"""
    raw_value = os.getenv(key)

    if raw_value is None or raw_value.strip() == "":
        return default

    value = raw_value.strip().lower()

    if value in TRUE_VALUES:
        return True

    if value in FALSE_VALUES:
        return False

    raise ValueError(
        f"{key} は true / false 形式で指定してください。現在の値: {raw_value}"
    )


def get_backend() -> str:
    """環境変数から LLM バックエンドを取得する"""
    backend = os.getenv("LLM_BACKEND", "ollama").strip().lower()
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(
            f"LLM_BACKEND は {', '.join(sorted(SUPPORTED_BACKENDS))} の"
            f"いずれかを指定してください。現在の値: {backend}"
        )
    return backend


def dedupe_preserve_order(items: list[str]) -> list[str]:
    """順序を保ったまま重複を除去する"""
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def resolve_enum_member(enum_cls: Any, raw_name: str) -> Any | None:
    """Enum メンバーを名前または値から解決する"""
    target = raw_name.strip().upper()

    for member in enum_cls:
        if member.name.upper() == target:
            return member

        member_value = str(getattr(member, "value", "")).strip().upper()
        if member_value == target:
            return member

    return None


def normalize_benchmark_names(
    benchmark_names: list[str],
) -> tuple[list[str], list[str]]:
    """ベンチマーク名を正規化する"""
    normalized: list[str] = []
    unknown: list[str] = []

    for name in benchmark_names:
        canonical = SUPPORTED_BENCHMARKS.get(name.strip().lower())
        if canonical is None:
            unknown.append(name)
        else:
            normalized.append(canonical)

    return dedupe_preserve_order(normalized), dedupe_preserve_order(unknown)


def ensure_timeout_settings() -> None:
    """deepeval のタイムアウト設定がなければデフォルト値を設定する"""
    defaults = {
        "DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE": "900",
        "DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE": "600",
        "DEEPEVAL_RETRY_MAX_ATTEMPTS": "2",
    }
    for key, default_value in defaults.items():
        if not os.getenv(key):
            os.environ[key] = default_value


def load_validated_config() -> tuple[str, list[str], list[str]]:
    """環境変数を読み込み、検証済みの (backend, models, benchmarks) を返す

    ベンチマーク設定値の事前検証も行う。
    """
    from benchmarks import BENCHMARK_FACTORIES

    backend = get_backend()
    raw_model_names = get_env_list("BENCHMARK_MODELS")
    raw_benchmark_names = get_env_list("BENCHMARK_TYPES")

    # モデル・ベンチマーク名の正規化と重複除去
    normalized_models = dedupe_preserve_order(raw_model_names)
    normalized_benchmarks, unknown_benchmarks = normalize_benchmark_names(
        raw_benchmark_names
    )

    if not normalized_models:
        raise ValueError(
            "BENCHMARK_MODELS が設定されていません。"
            " .env ファイルの BENCHMARK_MODELS にモデル名を記入してください。"
        )

    if not raw_benchmark_names:
        raise ValueError(
            "BENCHMARK_TYPES が設定されていません。"
            " .env ファイルの BENCHMARK_TYPES にベンチマーク名を記入してください。"
        )

    if unknown_benchmarks:
        print(f"[警告] 未対応のベンチマーク: {', '.join(unknown_benchmarks)}")
        print(
            f"  → 対応ベンチマーク: "
            f"{', '.join(BENCHMARK_FACTORIES.keys())}"
        )

    if not normalized_benchmarks:
        raise ValueError(
            "BENCHMARK_TYPES に有効なベンチマークがありません。"
            f" 対応ベンチマーク: {', '.join(BENCHMARK_FACTORIES.keys())}"
        )

    if len(normalized_models) < len(raw_model_names):
        print("[注意] 重複したモデル名は 1 回にまとめて実行します。")

    if len(normalized_benchmarks) < len(raw_benchmark_names):
        print("[注意] 重複したベンチマーク名は 1 回にまとめて実行します。")

    # ベンチマーク設定値の事前検証（生成してみてエラーがないか確認）
    for benchmark_name in normalized_benchmarks:
        factory = BENCHMARK_FACTORIES[benchmark_name]
        factory()

    return backend, normalized_models, normalized_benchmarks
