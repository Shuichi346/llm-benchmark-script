"""
ローカルLLMベンチマーク比較ツール

deepeval の公開ベンチマーク（MMLU, TruthfulQA, GSM8K）を使い、
Ollama または LM Studio で動作する複数のモデルを同一条件で評価・比較する。
"""

import datetime
import os
import sys
from typing import Any

from config import load_env, ensure_timeout_settings, load_validated_config
from benchmarks import run_single_benchmark, BENCHMARK_FACTORIES
from reporting import (
    format_score,
    save_results,
    print_summary_table,
    print_task_detail_tables,
)
from models import create_model, preflight_check, get_backend_display_info


def main() -> None:
    """全モデル × 全ベンチマークを順番に実行するメイン処理"""
    load_env()
    ensure_timeout_settings()

    try:
        backend, model_names, benchmark_names = load_validated_config()
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
    print(
        f" タイムアウト: "
        f"タスク="
        f"{os.getenv('DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE', 'default')}秒, "
        f"試行="
        f"{os.getenv('DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE', 'default')}秒"
    )
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
