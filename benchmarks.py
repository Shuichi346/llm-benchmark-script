"""
ベンチマークの生成・実行ロジック

環境変数に基づいて MMLU / TruthfulQA / GSM8K のインスタンスを生成し、
モデルに対して実行する。
"""

import inspect
import os
from typing import Any, Callable

from deepeval.benchmarks import GSM8K, MMLU, TruthfulQA
from deepeval.benchmarks.modes import TruthfulQAMode
from deepeval.benchmarks.tasks import MMLUTask, TruthfulQATask
from deepeval.models import DeepEvalBaseLLM

from config import (
    get_env_bool,
    get_env_int,
    get_env_list,
    dedupe_preserve_order,
    resolve_enum_member,
)


def _build_instance(factory: Callable[..., Any], kwargs: dict[str, Any]) -> Any:
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

    filtered_kwargs = {
        key: value for key, value in kwargs.items() if key in parameters
    }
    dropped_keys = [key for key in kwargs if key not in filtered_kwargs]

    if dropped_keys:
        factory_name = getattr(factory, "__name__", factory.__class__.__name__)
        print(
            f"  [注意] {factory_name} では "
            f"{', '.join(dropped_keys)} を使えないため無視します。"
        )

    return factory(**filtered_kwargs)


def _resolve_tasks(
    enum_cls: Any,
    task_names: list[str],
    env_key_name: str,
) -> list[Any] | None:
    """タスク名のリストを対応する Enum メンバーに変換する

    enum_cls: MMLUTask や TruthfulQATask などの Enum クラス
    task_names: 環境変数から取得したタスク名リスト
    env_key_name: エラーメッセージ用の環境変数名
    """
    if not task_names:
        return None

    resolved_tasks: list[Any] = []
    invalid_tasks: list[str] = []

    for task_name in task_names:
        member = resolve_enum_member(enum_cls, task_name)
        if member is None:
            invalid_tasks.append(task_name)
        else:
            resolved_tasks.append(member)

    if invalid_tasks:
        print(f"  [警告] 不明な {env_key_name} タスク: {', '.join(invalid_tasks)}")

    if not resolved_tasks:
        raise ValueError(
            f"{env_key_name} に有効なタスクが 1 つもありません。"
            "タスク名を見直してください。"
        )

    # 重複を除去（name ベースで判定）
    seen_names: set[str] = set()
    unique_tasks: list[Any] = []

    for task in resolved_tasks:
        if task.name not in seen_names:
            seen_names.add(task.name)
            unique_tasks.append(task)

    return unique_tasks


def _create_mmlu_benchmark() -> MMLU:
    """環境変数に基づいて MMLU ベンチマークを生成する"""
    task_names = get_env_list("MMLU_TASKS")
    n_shots = get_env_int("MMLU_N_SHOTS", 5, minimum=0, maximum=5)

    kwargs: dict[str, Any] = {"n_shots": n_shots}

    tasks = _resolve_tasks(MMLUTask, task_names, "MMLU_TASKS")
    if tasks is not None:
        kwargs["tasks"] = tasks

    return _build_instance(MMLU, kwargs)


def _create_truthfulqa_benchmark() -> TruthfulQA:
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
    tasks = _resolve_tasks(TruthfulQATask, task_names, "TRUTHFULQA_TASKS")
    if tasks is not None:
        kwargs["tasks"] = tasks

    return _build_instance(TruthfulQA, kwargs)


def _create_gsm8k_benchmark() -> GSM8K:
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

    return _build_instance(GSM8K, kwargs)


BENCHMARK_FACTORIES: dict[str, Callable[[], Any]] = {
    "MMLU": _create_mmlu_benchmark,
    "TruthfulQA": _create_truthfulqa_benchmark,
    "GSM8K": _create_gsm8k_benchmark,
}


def normalize_score(value: Any) -> float | None:
    """スコアを float に正規化する"""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _serialize_task_scores(task_scores: Any) -> Any | None:
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

    overall_score = normalize_score(
        getattr(benchmark, "overall_score", None)
    )

    if overall_score is None and hasattr(evaluation_result, "overall_score"):
        overall_score = normalize_score(
            getattr(evaluation_result, "overall_score")
        )

    if overall_score is None:
        overall_score = normalize_score(evaluation_result)

    result: dict[str, Any] = {"overall_score": overall_score}

    task_scores = _serialize_task_scores(
        getattr(benchmark, "task_scores", None)
    )
    if task_scores is not None:
        result["task_scores"] = task_scores

    return result
