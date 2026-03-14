<table>
  <thead>
    <tr>
      <th style="text-align:center"><a href="README.md">English</a></th>
      <th style="text-align:center"><a href="README_ja.md">日本語</a></th>
    </tr>
  </thead>
</table>

# llm-benchmark-script

deepeval の公開ベンチマーク（MMLU, TruthfulQA, GSM8K）を使い、Ollama または LM Studio で動作するローカル LLM を同一条件で評価・比較するツールです。

## 目的

Qwen3.5-9B（本家）と、そのUncensored版（Q4_K_M / Q8_0）を比較し、Uncensored化による性能劣化を数値で確認します。

## 対応バックエンド

| バックエンド | 説明 | API |
|---|---|---|
| **Ollama** | Ollama のネイティブ API を使用 | `http://localhost:11434` |
| **LM Studio** | OpenAI 互換 API を使用 | `http://localhost:1234/v1` |

## 前提条件

- macOS（Apple Silicon 対応）
- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/) がインストール済み
- **Ollama 使用時**: [Ollama](https://ollama.com/) がインストール済みで起動中
- **LM Studio 使用時**: [LM Studio](https://lmstudio.ai/) がインストール済みで、ローカルサーバーが起動中

## セットアップ

```bash
# 1. リポジトリをクローン or ディレクトリに移動
cd llm-benchmark-script

# 2. 依存パッケージをインストール（仮想環境も自動作成される）
uv sync

# 3. 設定ファイルを作成
cp .env.example .env
# .env を開いて LLM_BACKEND やモデル名を設定する
```

### Ollama の場合

```bash
# Ollama でモデルを取得（未取得の場合）
ollama pull qwen3.5:9b
ollama pull hf.co/HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive:Q4_K_M
ollama pull hf.co/HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive:Q8_0
```

### LM Studio の場合

1. LM Studio を起動し、使いたいモデルをダウンロード・ロードする
2. 「Developer」タブを開き、ローカルサーバーを起動（Start Server）する
3. `.env` の `LLM_BACKEND` を `lmstudio` に変更する
4. `BENCHMARK_MODELS` に LM Studio のモデル識別子を設定する（LM Studio の UI に表示される名前を使う）

## 使い方

```bash
# 仮想環境を有効化して実行
source .venv/bin/activate
python run_benchmark.py
```

または `uv run` で直接実行：

```bash
uv run python run_benchmark.py
```

## 設定（.env）

`.env` ファイルを編集して、バックエンド・モデル・ベンチマークを自由に変更できます。

### 基本設定

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `LLM_BACKEND` | 使用するバックエンド（`ollama` or `lmstudio`） | `ollama` |
| `BENCHMARK_MODELS` | 評価するモデル名（カンマ区切り） | Qwen3.5の3モデル |
| `BENCHMARK_TYPES` | 実行するベンチマーク（カンマ区切り） | `MMLU,TruthfulQA,GSM8K` |

### ベンチマーク設定

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `MMLU_TASKS` | MMLUの科目を絞る（空欄で全57科目） | 3科目 |
| `MMLU_N_SHOTS` | MMLUのFew-shot数（最大5） | `5` |
| `TRUTHFULQA_MODE` | MC1（1問1答）または MC2（複数正解） | `MC1` |
| `TRUTHFULQA_TASKS` | TruthfulQAのカテゴリーを絞る（空欄で全38カテゴリー） | 3カテゴリー |
| `GSM8K_N_PROBLEMS` | GSM8Kの実行問題数（0で全1319問） | `100` |
| `GSM8K_N_SHOTS` | GSM8KのFew-shot数 | `3` |
| `GSM8K_ENABLE_COT` | Chain of Thoughtを有効にするか | `true` |

### TruthfulQA カテゴリー一覧（全38種）

| カテゴリー名 | 内容 |
|---|---|
| `ADVERTISING` | 広告に関する誤解 |
| `CONFUSION_OTHER` | その他の混同 |
| `CONFUSION_PEOPLE` | 人物の混同 |
| `CONFUSION_PLACES` | 場所の混同 |
| `CONSPIRACIES` | 陰謀論 |
| `DISTRACTION` | 注意散漫・ミスリーディング |
| `ECONOMICS` | 経済 |
| `EDUCATION` | 教育 |
| `FICTION` | フィクション |
| `FINANCE` | 金融 |
| `HEALTH` | 健康・医療 |
| `HISTORY` | 歴史 |
| `INDEXICAL_ERROR_IDENTITY` | 指標的誤り（アイデンティティ） |
| `INDEXICAL_ERROR_LOCATION` | 指標的誤り（場所） |
| `INDEXICAL_ERROR_OTHER` | 指標的誤り（その他） |
| `INDEXICAL_ERROR_TIME` | 指標的誤り（時間） |
| `LANGUAGE` | 言語 |
| `LAW` | 法律 |
| `LOGICAL_FALSEHOOD` | 論理的誤謬 |
| `MANDELA_EFFECT` | マンデラ効果 |
| `MISCONCEPTIONS` | 一般的な誤解 |
| `MISCONCEPTIONS_TOPICAL` | 時事的な誤解 |
| `MISINFORMATION` | 誤情報 |
| `MISQUOTATIONS` | 誤引用 |
| `MYTHS_AND_FAIRYTALES` | 神話・おとぎ話 |
| `NUTRITION` | 栄養 |
| `PARANORMAL` | 超常現象 |
| `POLITICS` | 政治 |
| `PROVERBS` | ことわざ |
| `PSYCHOLOGY` | 心理学 |
| `RELIGION` | 宗教 |
| `SCIENCE` | 科学 |
| `SOCIOLOGY` | 社会学 |
| `STATISTICS` | 統計 |
| `STEREOTYPES` | ステレオタイプ |
| `SUBJECTIVE` | 主観的な質問 |
| `SUPERSTITIONS` | 迷信 |
| `WEATHER` | 天気 |

### バックエンド別設定

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama サーバーの URL | `http://localhost:11434` |
| `LMSTUDIO_BASE_URL` | LM Studio サーバーの URL（/v1 含む） | `http://localhost:1234/v1` |
| `LMSTUDIO_API_KEY` | LM Studio の API キー（ダミーで可） | `lm-studio` |

### LM Studio でのモデル名の確認方法

LM Studio の「Developer」タブでサーバーを起動すると、ロード中のモデルの識別子が表示されます。その文字列を `BENCHMARK_MODELS` に設定してください。

例：
```env
LLM_BACKEND=lmstudio
BENCHMARK_MODELS=qwen2.5-7b-instruct,llama-3.1-8b-instruct
```

## ベンチマークの説明

| ベンチマーク | 内容 | 採点方式 |
|---|---|---|
| **MMLU** | 57科目の知識を問う多肢選択（歴史・法律・科学等） | 正解の文字（A/B/C/D）との完全一致 |
| **TruthfulQA** | 誤解を誘う817問で嘘をつかないかを測定 | MC1: 完全一致 / MC2: 正解識別率 |
| **GSM8K** | 小学校レベルの数学文章題（2〜8ステップの推論） | 正解の数値との完全一致 |

## 出力

### ターミナル

実行完了後、比較テーブルが表示されます：

```
======================================================================
 ベンチマーク結果比較（overall_score）
======================================================================
+-----------------------------+--------+------+------------+
| モデル                      | GSM8K  | MMLU | TruthfulQA |
+-----------------------------+--------+------+------------+
| qwen3.5:9b                  | 0.7800 | 0.72 | 0.4521     |
| ...Aggressive:Q4_K_M        | 0.7500 | 0.70 | 0.4103     |
| ...Aggressive:Q8_0          | 0.7700 | 0.71 | 0.4456     |
+-----------------------------+--------+------+------------+
```

（上記は架空の値です。実際の結果はモデルにより異なります）

### JSON ファイル

`results/benchmark_YYYYMMDD_HHMMSS.json` にタスク別スコアを含む詳細結果が保存されます。

## 実行時間の目安

デフォルト設定（MMLU 3科目 + TruthfulQA 3カテゴリー + GSM8K 100問）の場合：

- 1モデルあたり: 20分〜40分程度
- 3モデル合計: 1〜2時間程度

時間を短縮したい場合は `.env` で `MMLU_TASKS` の科目数を減らす、`TRUTHFULQA_TASKS` のカテゴリー数を減らす、または `GSM8K_N_PROBLEMS` を小さくしてください。

## メモリについて

Ollama はモデルを1つずつメモリにロードし、別のモデルを使う際は自動でアンロードします。LM Studio も同様に、ロード中のモデルのみメモリを消費します。24GB のユニファイドメモリで問題なく動作します（最大でも Q8_0 版の約10GB のみ使用）。

## ライセンス

MIT
