<table>
  <thead>
    <tr>
      <th style="text-align:center"><a href="README.md">English</a></th>
      <th style="text-align:center"><a href="README_ja.md">日本語</a></th>
    </tr>
  </thead>
</table>

# LLM Benchmark Script

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![deepeval](https://img.shields.io/badge/deepeval-3.8+-00B4D8)
![License](https://img.shields.io/badge/License-[MIT]-blue)
![Version](https://img.shields.io/badge/version-0.3.0-green)

**deepeval** の公開ベンチマーク（MMLU, TruthfulQA, GSM8K）を使い、**Ollama** または **LM Studio** で動作するローカルLLMを同一条件で評価・比較するコマンドラインツールです。

複数のモデルに対してベンチマークを一括実行し、スコアの比較表をターミナルに表示するとともに、結果をJSON形式で保存します。

---

## 目次

- [特徴](#特徴)
- [対応ベンチマーク](#対応ベンチマーク)
- [技術スタック](#技術スタック)
- [必要要件](#必要要件)
- [セットアップ](#セットアップ)
- [環境変数の設定](#環境変数の設定)
- [使い方](#使い方)
- [出力例](#出力例)
- [プロジェクト構成](#プロジェクト構成)
- [トラブルシューティング](#トラブルシューティング)
- [ライセンス](#ライセンス)

---

## 特徴

- **マルチバックエンド対応** — Ollama と LM Studio の両方をサポートし、環境変数ひとつで切り替え可能
- **3種類の標準ベンチマーク** — MMLU（知識）、TruthfulQA（真偽判定）、GSM8K（数学推論）に対応
- **柔軟な設定** — 科目・カテゴリー・問題数・Few-shot数などを `.env` ファイルで細かく制御
- **複数モデル一括比較** — 同一条件で複数モデルを順次評価し、比較表を自動生成
- **事前チェック機能** — ベンチマーク実行前にサーバー接続・モデル可用性を自動検証
- **結果の永続化** — タイムスタンプ付きJSONファイルに全結果（タスク別スコア含む）を保存
- **日本語対応のCLI出力** — ターミナルに見やすい比較テーブルを表示

---

## 対応ベンチマーク

| ベンチマーク | 概要 | 評価内容 |
|---|---|---|
| **MMLU** | Massive Multitask Language Understanding | 57科目にわたる知識・理解力（Few-shot対応） |
| **TruthfulQA** | Truthful Question Answering | 事実に基づく正確な回答能力（MC1/MC2モード） |
| **GSM8K** | Grade School Math 8K | 小学校レベルの算数文章題（Chain of Thought対応） |

---

## 技術スタック

| カテゴリー | 技術 |
|---|---|
| 言語 | Python 3.12+ |
| ベンチマーク基盤 | deepeval (≥3.8.0) |
| LLMバックエンド | Ollama (ollama ≥0.4.0) / LM Studio (openai ≥1.0.0) |
| 設定管理 | python-dotenv (≥1.0.0) |
| テーブル表示 | tabulate (≥0.9.0) |

---

## 必要要件

- **Python 3.12** 以上
- **Ollama** または **LM Studio** がローカルで起動していること
- 評価対象のモデルが事前にダウンロード・ロード済みであること

---

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/Shuichi346/llm-benchmark-script
cd llm-benchmark-script
```

### 2. 依存パッケージのインストール

**uv を使用する場合（推奨）:**

```bash
uv sync
```

**pip を使用する場合:**

```bash
pip install .
```

### 3. 環境変数ファイルの作成

```bash
cp .env.example .env
```

コピーした `.env` ファイルを編集し、使用するバックエンドやモデルに合わせて設定を調整してください。

### 4. LLMバックエンドの準備

**Ollama の場合:**

```bash
# Ollama サーバーを起動
ollama serve

# モデルをダウンロード（例）
ollama pull qwen3:8b
```

**LM Studio の場合:**

LM Studio を起動し、「Developer」タブからローカルサーバーを Start してください。評価対象のモデルを事前にロードしておく必要があります。

---

## 環境変数の設定

`.env` ファイルで全ての設定を管理します。以下に設定項目の一覧を示します。

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

### バックエンド別設定

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama サーバーの URL | `http://localhost:11434` |
| `LMSTUDIO_BASE_URL` | LM Studio サーバーの URL（/v1 含む） | `http://localhost:1234/v1` |
| `LMSTUDIO_API_KEY` | LM Studio の API キー（ダミーで可） | `lm-studio` |

### deepeval タイムアウト設定

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE` | 1問あたりの最大待機時間（秒） | `900` |
| `DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE` | 1回のAPI呼び出しの最大待機時間（秒） | `600` |
| `DEEPEVAL_RETRY_MAX_ATTEMPTS` | リトライ回数 | `2` |

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

---

## 使い方

### 基本的な実行

```bash
python run_benchmark.py
```

または、パッケージとしてインストール済みの場合は以下のコマンドでも実行できます。

```bash
llm-benchmark
```

### 実行の流れ

ツールは以下の順序で処理を行います。

1. `.env` ファイルから設定を読み込み、バリデーションを実行
2. 指定されたバックエンド（Ollama / LM Studio）への接続を確認
3. 各モデルの存在・ロード状態をテスト生成で検証
4. 全モデル × 全ベンチマークの組み合わせを順次実行
5. 結果を `results/` ディレクトリにJSON形式で保存
6. ターミナルに比較サマリーテーブルとタスク別詳細テーブルを表示

### 実行中の中断

`Ctrl+C` でいつでも安全に中断できます。

---

## 出力例

### ターミナル出力

```
======================================================================
 ローカルLLMベンチマーク比較ツール
======================================================================
 バックエンド: Ollama
 対象モデル数: 2
   1. qwen3:8b
   2. qwen3:4b
 実行ベンチマーク: MMLU, TruthfulQA, GSM8K
 サーバー: http://localhost:11434
======================================================================

======================================================================
 ベンチマーク結果比較（overall_score）
======================================================================
+------------+--------+------------+--------+
| モデル     | MMLU   | TruthfulQA | GSM8K  |
+------------+--------+------------+--------+
| qwen3:8b   | 0.7200 | 0.5400     | 0.8100 |
| qwen3:4b   | 0.6500 | 0.4800     | 0.7200 |
+------------+--------+------------+--------+
```

### JSON出力

結果は `results/benchmark_YYYYMMDD_HHMMSS.json` に保存されます。タイムスタンプ、Python バージョン、バックエンド情報、各モデルの overall_score およびタスク別スコアが含まれます。

---

## プロジェクト構成

```
llm-benchmark-script/
├── run_benchmark.py     # メインエントリーポイント
├── config.py            # 環境変数の読み込み・バリデーション
├── benchmarks.py        # ベンチマーク生成・実行ロジック
├── reporting.py         # 結果の保存・テーブル表示
├── models/
│   ├── __init__.py      # バックエンド振り分けインターフェース
│   ├── ollama_model.py  # Ollama バックエンド実装
│   └── lmstudio_model.py  # LM Studio バックエンド実装
├── results/             # ベンチマーク結果の保存先（JSON）
│   └── .gitkeep
├── .env.example         # 環境変数テンプレート
├── pyproject.toml       # プロジェクト設定・依存関係
├── .python-version      # Python バージョン指定
└── .gitignore
```

---

## トラブルシューティング

### サーバーに接続できない

Ollama の場合は `ollama serve` でサーバーが起動しているか確認してください。LM Studio の場合は「Developer」タブでローカルサーバーが Start されているか確認してください。

### モデルがスキップされる

指定したモデルがバックエンドにダウンロード・ロードされていない可能性があります。Ollama の場合は `ollama list` で、LM Studio の場合はアプリ上でモデルの状態を確認してください。

### タイムアウトが発生する

ローカルLLMは応答に時間がかかる場合があります。`.env` の `DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE` と `DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE` の値を大きくしてください。9Bクラスのモデルでは600〜900秒を推奨します。

### 全科目・全カテゴリーの実行に時間がかかる

MMLU は57科目、TruthfulQA は38カテゴリー（817問）、GSM8K は1319問あります。初回は `MMLU_TASKS`、`TRUTHFULQA_TASKS`、`GSM8K_N_PROBLEMS` で対象を絞って実行することをおすすめします。

---

## ライセンス

MIT
