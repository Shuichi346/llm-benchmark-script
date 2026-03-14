<table>
  <thead>
    <tr>
      <th style="text-align:center"><a href="README.md">English</a></th>
      <th style="text-align:center"><a href="README_ja.md">日本語</a></th>
    </tr>
  </thead>
</table>

# ローカルLLMベンチマーク比較ツール

[deepeval](https://github.com/confident-ai/deepeval) の公開ベンチマーク（MMLU, TruthfulQA, GSM8K）を使い、**Ollama** または **LM Studio** で動作する複数のローカルLLMモデルを同一条件で評価・比較するコマンドラインツールです。

## 特徴

- **複数モデルの一括評価** — 指定した複数のモデルに対して、選択したベンチマークを順番に実行し、結果を横並びで比較できます。
- **2つのバックエンドに対応** — Ollama と LM Studio（OpenAI互換API）のどちらでも利用可能です。
- **3種類のベンチマーク** — MMLU（知識・推論）、TruthfulQA（真実性）、GSM8K（算数）に対応しています。
- **柔軟な設定** — `.env` ファイルでモデル名、ベンチマーク種別、科目・カテゴリの絞り込み、問題数、タイムアウトなどを細かく制御できます。
- **事前チェック機能** — ベンチマーク実行前にサーバーへの接続確認とモデルの動作確認を行い、問題があるモデルは自動的にスキップします。
- **結果の保存と表示** — 実行結果をタイムスタンプ付きのJSONファイルに保存し、ターミナル上に比較テーブルとタスク別詳細テーブルを表示します。

## 動作要件

- Python 3.12 以上
- 以下のいずれかのローカルLLMランタイム:
  - [Ollama](https://ollama.com/) — 起動済みであること（`ollama serve`）
  - [LM Studio](https://lmstudio.ai/) — ローカルサーバーが起動済みであること（Developerタブ → Server Start）

## インストール

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd llm-benchmark-script
```

### 2. Python 環境の準備

[uv](https://docs.astral.sh/uv/) を使用する場合:

```bash
uv sync
```

pip を使用する場合:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install .
```

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを編集し、使用するバックエンドやモデル名を設定してください。

## 設定項目

`.env` ファイルで以下の項目を設定します。詳細なテンプレートは `.env.example` を参照してください。

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

`TRUTHFULQA_TASKS` に指定できるカテゴリーの一覧です。カンマ区切りで複数指定できます。空欄にすると全カテゴリーが対象になります。

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

### タイムアウト設定

ローカルLLMは応答速度が遅いため、deepeval のデフォルトタイムアウトでは不足する場合があります。環境に合わせて調整してください。

| 環境変数 | 説明 | デフォルト |
|---|---|---|
| `DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE` | 1問あたりの最大待機時間（秒） | `900` |
| `DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE` | 1回のAPI呼び出しの最大待機時間（秒） | `600` |
| `DEEPEVAL_RETRY_MAX_ATTEMPTS` | リトライ回数 | `2` |

## 使い方

### 実行

```bash
python run_benchmark.py
```

または、パッケージとしてインストール済みの場合:

```bash
llm-benchmark
```

### 実行の流れ

1. `.env` ファイルから設定を読み込み、バリデーションを実行
2. バックエンド（Ollama / LM Studio）への接続確認
3. 各モデルの動作確認（テスト生成で応答を検証）
4. 全モデル × 全ベンチマークを順番に実行
5. 結果をJSONファイルに保存（`results/` ディレクトリ）
6. ターミナルに比較テーブルとタスク別詳細テーブルを表示

### 出力例

ターミナルには以下のような比較テーブルが表示されます:

```
======================================================================
 ベンチマーク結果比較（overall_score）
======================================================================
+--------------------+--------+--------------+--------+
| モデル             | MMLU   | TruthfulQA   | GSM8K  |
+====================+========+==============+========+
| gemma2:9b          | 0.6000 | 0.4133       | 0.7800 |
+--------------------+--------+--------------+--------+
| llama3.1:8b        | 0.5333 | 0.3800       | 0.7200 |
+--------------------+--------+--------------+--------+
```

結果はJSONファイルとしても `results/benchmark_YYYYMMDD_HHMMSS.json` に保存されます。

## ディレクトリ構成

```
llm-benchmark-script/
├── run_benchmark.py      # メインエントリポイント
├── config.py             # 環境変数の読み込み・バリデーション
├── benchmarks.py         # ベンチマークの生成・実行ロジック
├── reporting.py          # 結果の保存・テーブル表示
├── models/
│   ├── __init__.py       # バックエンド振り分けの統合インターフェース
│   ├── ollama_model.py   # Ollama バックエンド実装
│   └── lmstudio_model.py # LM Studio バックエンド実装
├── results/              # ベンチマーク結果の保存先（JSON）
│   └── .gitkeep
├── .env.example          # 環境変数の設定テンプレート
├── pyproject.toml        # プロジェクト定義・依存パッケージ
├── .python-version       # Python バージョン指定（3.12）
└── .gitignore
```

## 依存パッケージ

| パッケージ | 用途 |
|---|---|
| [deepeval](https://github.com/confident-ai/deepeval) (>=3.8.0) | ベンチマーク実行フレームワーク |
| [python-dotenv](https://github.com/theskumar/python-dotenv) (>=1.0.0) | `.env` ファイルの読み込み |
| [ollama](https://github.com/ollama/ollama-python) (>=0.4.0) | Ollama Python クライアント |
| [openai](https://github.com/openai/openai-python) (>=1.0.0) | LM Studio の OpenAI互換APIクライアント |
| [tabulate](https://github.com/astanin/python-tabulate) (>=0.9.0) | ターミナルへのテーブル表示 |

## 注意事項

- ローカルLLMの応答速度はハードウェア性能に大きく依存します。GPUメモリが不足する場合、実行速度が著しく低下したりタイムアウトが発生する可能性があります。タイムアウト設定は環境に合わせて調整してください。
- 全科目・全問での実行は非常に長時間かかります。初回は科目や問題数を絞って試すことを推奨します。
- LM Studio バックエンドでは、LLMの応答テキストからベンチマークの正解値（A/B/C/D、数値など）を正規表現で抽出するクリーニング処理を行っています。モデルの出力形式によっては正しく抽出できない場合があります。
- `Ctrl+C` で実行を中断できます。

## ライセンス

MIT
