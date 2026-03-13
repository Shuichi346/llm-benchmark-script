"""
ベンチマーク結果の保存・表示

JSON ファイルへの保存と、ターミナルへのテーブル表示を担当する。
"""

import datetime
import json
import os
from typing import Any

from tabulate import tabulate

from benchmarks import normalize_score


def format_score(value: Any) -> str:
    """スコア表示用の文字列に変換する"""
    score = normalize_score(value)
    if score is None:
        return "N/A"
    return f"{score:.4f}"


def _get_short_name(model_name: str) -> str:
    """長いモデル名を表示用に短縮する"""
    if "/" in model_name:
        return model_name.split("/")[-1]
    return model_name


def save_results(all_results: dict[str, Any], output_dir: str = "results") -> str:
    """全結果をタイムスタンプ付き JSON ファイルに保存する"""
    os.makedirs(output_dir, exist_ok=True)

    now = datetime.datetime.now().astimezone()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"benchmark_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(all_results, file, ensure_ascii=False, indent=2, default=str)

    return filepath


def _extract_task_and_score(
    record: dict[str, Any],
) -> tuple[str | None, float | None]:
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
        row = [_get_short_name(model_name)]

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

                task_name, score = _extract_task_and_score(record)
                if task_name is None:
                    continue

                model_task_scores[model_name][task_name] = score
                all_task_names.add(task_name)

        if not all_task_names:
            continue

        print(f"--- {benchmark_name} タスク別スコア ---")

        model_names = list(results.keys())
        headers = ["タスク"] + [_get_short_name(name) for name in model_names]
        rows: list[list[str]] = []

        for task_name in sorted(all_task_names):
            row = [task_name]

            for model_name in model_names:
                score = model_task_scores.get(model_name, {}).get(task_name)
                row.append("-" if score is None else format_score(score))

            rows.append(row)

        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print()
