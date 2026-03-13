"""
ローカルLLMベンチマーク比較ツール

deepeval の公開ベンチマーク（MMLU, TruthfulQA, GSM8K）を使い、
Ollama または LM Studio で動作する複数のモデルを同一条件で評価・比較する。
設定は .env ファイルで管理する。
"""

import datetime
import inspect
import json
import os
import sys
from typing import Any, Callable

from deepeval.benchmarks import GSM8K, MMLU, TruthfulQA
from deepeval.benchmarks.modes import TruthfulQAMode
from deepeval.benchmarks.tasks import MMLUTask, TruthfulQATask
from deepeval.models import DeepEvalBaseLLM
from dotenv import load_dotenv
from tabulate import tabulate

from models import create_model, preflight_check, get_backend_display_info


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


def normalize_benchmark_names(benchmark_names: list[str]) -> tuple[list[str], list[str]]:
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


def build_instance(factory: Callable[..., Any], kwargs: dict[str, Any]) -> Any:
    """利用可能な引数だけを渡してインスタンスを生成する"""
    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        return factory(**kwargs)

    parameters = signature.parameters
    accepts_var_keyword = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )

    if accepts_var_keyword:
        return factory(**kwargs)

    filtered_kwargs = {key: value for key, value in kwargs.items() if key in parameters}
    dropped_keys = [key for key in kwargs if key not in filtered_kwargs]

    if dropped_keys:
        factory_name = getattr(factory, "__name__", factory.__class__.__name__)
        print(
            f"  [注意] {factory_name} では "
            f"{', '.join(dropped_keys)} を使えないため無視します。"
        )

    return factory(**filtered_kwargs)


def resolve_mmlu_tasks(task_names: list[str]) -> list[Any] | None:
    """MMLU タスク名を enum に変換する"""
    if not task_names:
        return None

    resolved_tasks: list[Any] = []
    invalid_tasks: list[str] = []

    for task_name in task_names:
        member = resolve_enum_member(MMLUTask, task_name)
        if member is None:
            invalid_tasks.append(task_name)
        else:
            resolved_tasks.append(member)

    if invalid_tasks:
        print(f"  [警告] 不明な MMLU タスク: {', '.join(invalid_tasks)}")

    if not resolved_tasks:
        raise ValueError(
            "MMLU_TASKS に有効なタスクが 1 つもありません。"
            "タスク名を見直してください。"
        )

    unique_tasks: list[Any] = []
    seen_names: set[str] = set()

    for task in resolved_tasks:
        if task.name not in seen_names:
            seen_names.add(task.name)
            unique_tasks.append(task)

    return unique_tasks


def resolve_truthfulqa_tasks(task_names: list[str]) -> list[Any] | None:
    """TruthfulQA タスク名を enum に変換する"""
    if not task_names:
        return None

    resolved_tasks: list[Any] = []
    invalid_tasks: list[str] = []

    for task_name in task_names:
        member = resolve_enum_member(TruthfulQATask, task_name)
        if member is None:
            invalid_tasks.append(task_name)
        else:
            resolved_tasks.append(member)

    if invalid_tasks:
        print(f"  [警告] 不明な TruthfulQA タスク: {', '.join(invalid_tasks)}")

    if not resolved_tasks:
        raise ValueError(
            "TRUTHFULQA_TASKS に有効なタスクが 1 つもありません。"
            "タスク名を見直してください。"
        )

    unique_tasks: list[Any] = []
    seen_names: set[str] = set()

    for task in resolved_tasks:
        if task.name not in seen_names:
            seen_names.add(task.name)
            unique_tasks.append(task)

    return unique_tasks


def create_mmlu_benchmark() -> MMLU:
    """環境変数に基づいて MMLU ベンチマークを生成する"""
    task_names = get_env_list("MMLU_TASKS")
    n_shots = get_env_int("MMLU_N_SHOTS", 5, minimum=0, maximum=5)

    kwargs: dict[str, Any] = {
        "n_shots": n_shots,
    }

    tasks = resolve_mmlu_tasks(task_names)
    if tasks is not None:
        kwargs["tasks"] = tasks

    return build_instance(MMLU, kwargs)


def create_truthfulqa_benchmark() -> TruthfulQA:
    """環境変数に基づいて TruthfulQA ベンチマークを生成する"""
    mode_str = os.getenv("TRUTHFULQA_MODE", "MC1").strip()
    if not mode_str:
        mode_str = "MC1"

    mode = resolve_enum_member(TruthfulQAMode, mode_str)
    if mode is None:
        raise ValueError(
            "TRUTHFULQA_MODE は MC1 または MC2 を指定してください。"
            f"現在の値: {mode_str}"
        )

    kwargs: dict[str, Any] = {"mode": mode}

    task_names = get_env_list("TRUTHFULQA_TASKS")
    tasks = resolve_truthfulqa_tasks(task_names)
    if tasks is not None:
        kwargs["tasks"] = tasks

    return build_instance(TruthfulQA, kwargs)


def create_gsm8k_benchmark() -> GSM8K:
    """環境変数に基づいて GSM8K ベンチマークを生成する"""
    n_problems = get_env_int("GSM8K_N_PROBLEMS", 100, minimum=0)
    n_shots = get_env_int("GSM8K_N_SHOTS", 3, minimum=0)
    enable_cot = get_env_bool("GSM8K_ENABLE_COT", True)

    kwargs: dict[str, Any] = {
        "n_shots": n_shots,
        "enable_cot": enable_cot,
    }

    if n_problems > 0:
        kwargs["n_problems"] = n_problems

    return build_instance(GSM8K, kwargs)


BENCHMARK_FACTORIES: dict[str, Callable[[], Any]] = {
    "MMLU": create_mmlu_benchmark,
    "TruthfulQA": create_truthfulqa_benchmark,
    "GSM8K": create_gsm8k_benchmark,
}


def normalize_score(value: Any) -> float | None:
    """スコアを float に正規化する"""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def serialize_task_scores(task_scores: Any) -> Any | None:
    """task_scores を JSON 保存可能な形式へ変換する"""
    if task_scores is None:
        return None

    if hasattr(task_scores, "to_dict"):
        try:
            return task_scores.to_dict(orient="records")
        except TypeError:
            try:
                return task_scores.to_dict()
            except Exception:
                return str(task_scores)

    if isinstance(task_scores, (list, dict, str, int, float, bool)):
        return task_scores

    return str(task_scores)


def run_single_benchmark(
    model: DeepEvalBaseLLM, benchmark_name: str
) -> dict[str, Any]:
    """1つのモデルに対して1つのベンチマークを実行する"""
    factory = BENCHMARK_FACTORIES.get(benchmark_name)
    if factory is None:
        return {"error": f"未対応のベンチマークです: {benchmark_name}"}

    benchmark = factory()
    print(f"  ベンチマーク実行中: {benchmark_name} ...")

    try:
        evaluation_result = benchmark.evaluate(model=model)
    except Exception as exc:
        print(f"  [エラー] {benchmark_name} の実行に失敗: {exc}")
        return {"error": str(exc)}

    overall_score = normalize_score(getattr(benchmark, "overall_score", None))

    if overall_score is None and hasattr(evaluation_result, "overall_score"):
        overall_score = normalize_score(getattr(evaluation_result, "overall_score"))

    if overall_score is None:
        overall_score = normalize_score(evaluation_result)

    result: dict[str, Any] = {
        "overall_score": overall_score,
    }

    task_scores = serialize_task_scores(getattr(benchmark, "task_scores", None))
    if task_scores is not None:
        result["task_scores"] = task_scores

    return result


def save_results(all_results: dict[str, Any], output_dir: str = "results") -> str:
    """全結果をタイムスタンプ付き JSON ファイルに保存する"""
    os.makedirs(output_dir, exist_ok=True)

    now = datetime.datetime.now().astimezone()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"benchmark_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(all_results, file, ensure_ascii=False, indent=2, default=str)

    return filepath


def get_short_name(model_name: str) -> str:
    """長いモデル名を表示用に短縮する"""
    if "/" in model_name:
        return model_name.split("/")[-1]
    return model_name


def format_score(value: Any) -> str:
    """スコア表示用の文字列に変換する"""
    score = normalize_score(value)
    if score is None:
        return "N/A"
    return f"{score:.4f}"


def print_summary_table(all_results: dict[str, Any]) -> None:
    """全モデルの overall_score を比較するテーブルを表示する"""
    results = all_results.get("results", {})
    benchmark_names = all_results.get("metadata", {}).get("benchmarks", [])

    if not results or not benchmark_names:
        print("結果がありません。")
        return

    headers = ["モデル"] + benchmark_names
    rows: list[list[str]] = []

    for model_name, model_data in results.items():
        row = [get_short_name(model_name)]

        for benchmark_name in benchmark_names:
            benchmark_result = model_data.get(benchmark_name, {})

            if "error" in benchmark_result:
                row.append("ERROR")
            else:
                row.append(format_score(benchmark_result.get("overall_score")))

        rows.append(row)

    print("\n" + "=" * 70)
    print(" ベンチマーク結果比較（overall_score）")
    print("=" * 70)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()


def extract_task_and_score(record: dict[str, Any]) -> tuple[str | None, float | None]:
    """タスク別スコアの1行からタスク名とスコアを取り出す"""
    normalized_record = {
        str(key).strip().lower().replace(" ", "_"): value
        for key, value in record.items()
    }

    task_value = None
    for key in ("task", "task_name", "subject", "category"):
        if key in normalized_record:
            task_value = normalized_record[key]
            break

    score_value = None
    for key in ("score", "overall_score", "accuracy"):
        if key in normalized_record:
            score_value = normalized_record[key]
            break

    task_name = None if task_value is None else str(task_value)
    score = normalize_score(score_value)

    return task_name, score


def print_task_detail_tables(all_results: dict[str, Any]) -> None:
    """タスク別スコアの詳細テーブルを表示する"""
    results = all_results.get("results", {})
    benchmark_names = all_results.get("metadata", {}).get("benchmarks", [])

    for benchmark_name in benchmark_names:
        model_task_scores: dict[str, dict[str, float | None]] = {}
        all_task_names: set[str] = set()

        for model_name, model_data in results.items():
            benchmark_result = model_data.get(benchmark_name, {})
            task_scores = benchmark_result.get("task_scores")

            if not isinstance(task_scores, list):
                continue

            model_task_scores[model_name] = {}

            for record in task_scores:
                if not isinstance(record, dict):
                    continue

                task_name, score = extract_task_and_score(record)
                if task_name is None:
                    continue

                model_task_scores[model_name][task_name] = score
                all_task_names.add(task_name)

        if not all_task_names:
            continue

        print(f"--- {benchmark_name} タスク別スコア ---")

        model_names = list(results.keys())
        headers = ["タスク"] + [get_short_name(name) for name in model_names]
        rows: list[list[str]] = []

        for task_name in sorted(all_task_names):
            row = [task_name]

            for model_name in model_names:
                score = model_task_scores.get(model_name, {}).get(task_name)
                row.append("-" if score is None else format_score(score))

            rows.append(row)

        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print()


def validate_config(
    model_names: list[str],
    benchmark_names: list[str],
) -> tuple[list[str], list[str]]:
    """設定値を検証し、正規化済みの値を返す"""
    normalized_models = dedupe_preserve_order(model_names)
    normalized_benchmarks, unknown_benchmarks = normalize_benchmark_names(
        benchmark_names
    )

    if not normalized_models:
        raise ValueError(
            "BENCHMARK_MODELS が設定されていません。"
            " .env ファイルの BENCHMARK_MODELS にモデル名を記入してください。"
        )

    if not benchmark_names:
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

    if len(normalized_models) < len(model_names):
        print("[注意] 重複したモデル名は 1 回にまとめて実行します。")

    if len(normalized_benchmarks) < len(benchmark_names):
        print("[注意] 重複したベンチマーク名は 1 回にまとめて実行します。")

    return normalized_models, normalized_benchmarks


def validate_benchmark_settings(benchmark_names: list[str]) -> None:
    """ベンチマーク設定値を事前検証する"""
    for benchmark_name in benchmark_names:
        factory = BENCHMARK_FACTORIES[benchmark_name]
        factory()


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


def main() -> None:
    """全モデル × 全ベンチマークを順番に実行するメイン処理"""
    load_env()
    ensure_timeout_settings()

    try:
        backend = get_backend()
        raw_model_names = get_env_list("BENCHMARK_MODELS")
        raw_benchmark_names = get_env_list("BENCHMARK_TYPES")
        model_names, benchmark_names = validate_config(
            raw_model_names,
            raw_benchmark_names,
        )
        validate_benchmark_settings(benchmark_names)
    except ValueError as exc:
        print(f"[エラー] {exc}")
        sys.exit(1)

    # バックエンド別の事前チェック（接続確認・モデル確認）
    model_names = preflight_check(backend, model_names)

    # バックエンド表示情報を取得
    display_info = get_backend_display_info(backend)

    now = datetime.datetime.now().astimezone()

    print("=" * 70)
    print(" ローカルLLMベンチマーク比較ツール")
    print("=" * 70)
    print(f" バックエンド: {display_info['name']}")
    print(f" 対象モデル数: {len(model_names)}")
    for index, model_name in enumerate(model_names, start=1):
        print(f"   {index}. {model_name}")
    print(f" 実行ベンチマーク: {', '.join(benchmark_names)}")
    print(f" サーバー: {display_info['url']}")
    print(f" タイムアウト: "
          f"タスク={os.getenv('DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE', 'default')}秒, "
          f"試行={os.getenv('DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE', 'default')}秒")
    print("=" * 70)

    all_results: dict[str, Any] = {
        "metadata": {
            "timestamp": now.isoformat(),
            "python_version": sys.version,
            "backend": backend,
            "server_url": display_info["url"],
            "models": model_names,
            "benchmarks": benchmark_names,
        },
        "results": {},
    }

    total_benchmarks = len(model_names) * len(benchmark_names)
    current = 0

    for model_index, model_name in enumerate(model_names, start=1):
        print(f"\n{'─' * 70}")
        print(f" [{model_index}/{len(model_names)}] モデル: {model_name}")
        print(f"{'─' * 70}")

        model = create_model(backend, model_name)
        model_results: dict[str, Any] = {}

        for benchmark_name in benchmark_names:
            current += 1
            print(f"\n  ({current}/{total_benchmarks})")

            result = run_single_benchmark(model, benchmark_name)
            model_results[benchmark_name] = result

            if "error" in result:
                print(f"  → {benchmark_name} エラー: {result['error']}")
            else:
                print(
                    f"  → {benchmark_name} スコア: "
                    f"{format_score(result.get('overall_score'))}"
                )

        all_results["results"][model_name] = model_results

    filepath = save_results(all_results)
    print(f"\n結果を JSON に保存しました: {filepath}")

    print_summary_table(all_results)
    print_task_detail_tables(all_results)

    print("完了しました。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n中断しました。")
        sys.exit(130)
