<table>
  <thead>
    <tr>
      <th style="text-align:center"><a href="README_en.md">English</a></th>
      <th style="text-align:center">日本語</th>
    </tr>
  </thead>
</table>

# llm-benchmark-script

A tool to evaluate and compare local LLMs running on Ollama or LM Studio under identical conditions using deepeval's public benchmarks (MMLU, TruthfulQA, GSM8K).

## Purpose

To compare Qwen3.5-9B (original) with its Uncensored versions (Q4_K_M / Q8_0) and numerically confirm performance degradation caused by uncensoring.

## Supported Backends

| Backend | Description | API |
|---|---|---|
| **Ollama** | Uses Ollama's native API | `http://localhost:11434` |
| **LM Studio** | Uses OpenAI-compatible API | `http://localhost:1234/v1` |

## Prerequisites

- macOS (Apple Silicon supported)
- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) installed
- **When using Ollama**: [Ollama](https://ollama.com/) installed and running
- **When using LM Studio**: [LM Studio](https://lmstudio.ai/) installed with local server running

## Setup

```bash
# 1. Clone repository or navigate to directory
cd llm-benchmark-script

# 2. Install dependencies (virtual environment is automatically created)
uv sync

# 3. Create configuration file
cp .env.example .env
# Open .env and configure LLM_BACKEND and model names
```

### For Ollama

```bash
# Download models with Ollama (if not already downloaded)
ollama pull qwen3.5:9b
ollama pull hf.co/HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive:Q4_K_M
ollama pull hf.co/HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive:Q8_0
```

### For LM Studio

1. Launch LM Studio and download/load the desired models
2. Open the "Developer" tab and start the local server (Start Server)
3. Change `LLM_BACKEND` in `.env` to `lmstudio`
4. Set `BENCHMARK_MODELS` to the LM Studio model identifiers (use the names displayed in LM Studio's UI)

## Usage

```bash
# Activate virtual environment and run
source .venv/bin/activate
python run_benchmark.py
```

Or run directly with `uv run`:

```bash
uv run python run_benchmark.py
```

## Configuration (.env)

Edit the `.env` file to freely change backends, models, and benchmarks.

### Basic Settings

| Environment Variable | Description | Default |
|---|---|---|
| `LLM_BACKEND` | Backend to use (`ollama` or `lmstudio`) | `ollama` |
| `BENCHMARK_MODELS` | Model names to evaluate (comma-separated) | 3 Qwen3.5 models |
| `BENCHMARK_TYPES` | Benchmarks to run (comma-separated) | `MMLU,TruthfulQA,GSM8K` |

### Benchmark Settings

| Environment Variable | Description | Default |
|---|---|---|
| `MMLU_TASKS` | Limit MMLU subjects (empty for all 57 subjects) | 3 subjects |
| `MMLU_N_SHOTS` | Number of few-shots for MMLU (max 5) | `5` |
| `TRUTHFULQA_MODE` | MC1 (single answer) or MC2 (multiple correct answers) | `MC1` |
| `TRUTHFULQA_TASKS` | Limit TruthfulQA categories (empty for all 38 categories) | 3 categories |
| `GSM8K_N_PROBLEMS` | Number of GSM8K problems to run (0 for all 1319 problems) | `100` |
| `GSM8K_N_SHOTS` | Number of few-shots for GSM8K | `3` |
| `GSM8K_ENABLE_COT` | Enable Chain of Thought | `true` |

### TruthfulQA Categories (All 38 Types)

| Category Name | Content |
|---|---|
| `ADVERTISING` | Advertising misconceptions |
| `CONFUSION_OTHER` | Other confusions |
| `CONFUSION_PEOPLE` | People confusion |
| `CONFUSION_PLACES` | Place confusion |
| `CONSPIRACIES` | Conspiracy theories |
| `DISTRACTION` | Distraction/misleading |
| `ECONOMICS` | Economics |
| `EDUCATION` | Education |
| `FICTION` | Fiction |
| `FINANCE` | Finance |
| `HEALTH` | Health/medical |
| `HISTORY` | History |
| `INDEXICAL_ERROR_IDENTITY` | Indexical errors (identity) |
| `INDEXICAL_ERROR_LOCATION` | Indexical errors (location) |
| `INDEXICAL_ERROR_OTHER` | Indexical errors (other) |
| `INDEXICAL_ERROR_TIME` | Indexical errors (time) |
| `LANGUAGE` | Language |
| `LAW` | Law |
| `LOGICAL_FALSEHOOD` | Logical fallacies |
| `MANDELA_EFFECT` | Mandela effect |
| `MISCONCEPTIONS` | General misconceptions |
| `MISCONCEPTIONS_TOPICAL` | Topical misconceptions |
| `MISINFORMATION` | Misinformation |
| `MISQUOTATIONS` | Misquotations |
| `MYTHS_AND_FAIRYTALES` | Myths and fairy tales |
| `NUTRITION` | Nutrition |
| `PARANORMAL` | Paranormal |
| `POLITICS` | Politics |
| `PROVERBS` | Proverbs |
| `PSYCHOLOGY` | Psychology |
| `RELIGION` | Religion |
| `SCIENCE` | Science |
| `SOCIOLOGY` | Sociology |
| `STATISTICS` | Statistics |
| `STEREOTYPES` | Stereotypes |
| `SUBJECTIVE` | Subjective questions |
| `SUPERSTITIONS` | Superstitions |
| `WEATHER` | Weather |

### Backend-Specific Settings

| Environment Variable | Description | Default |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `LMSTUDIO_BASE_URL` | LM Studio server URL (including /v1) | `http://localhost:1234/v1` |
| `LMSTUDIO_API_KEY` | LM Studio API key (dummy is fine) | `lm-studio` |

### How to Check Model Names in LM Studio

When you start the server in LM Studio's "Developer" tab, the identifier of the loaded model will be displayed. Set that string in `BENCHMARK_MODELS`.

Example:
```env
LLM_BACKEND=lmstudio
BENCHMARK_MODELS=qwen2.5-7b-instruct,llama-3.1-8b-instruct
```

## Benchmark Descriptions

| Benchmark | Content | Scoring Method |
|---|---|---|
| **MMLU** | 57-subject knowledge multiple choice (history, law, science, etc.) | Exact match with correct letter (A/B/C/D) |
| **TruthfulQA** | 817 misleading questions to test if the model lies | MC1: exact match / MC2: correct identification rate |
| **GSM8K** | Elementary-level math word problems (2-8 step reasoning) | Exact match with correct numerical answer |

## Output

### Terminal

After completion, a comparison table is displayed:

```
======================================================================
 Benchmark Results Comparison (overall_score)
======================================================================
+-----------------------------+--------+------+------------+
| Model                       | GSM8K  | MMLU | TruthfulQA |
+-----------------------------+--------+------+------------+
| qwen3.5:9b                  | 0.7800 | 0.72 | 0.4521     |
| ...Aggressive:Q4_K_M        | 0.7500 | 0.70 | 0.4103     |
| ...Aggressive:Q8_0          | 0.7700 | 0.71 | 0.4456     |
+-----------------------------+--------+------+------------+
```

(The above values are fictional. Actual results vary by model)

### JSON File

Detailed results including task-specific scores are saved to `results/benchmark_YYYYMMDD_HHMMSS.json`.

## Estimated Runtime

With default settings (MMLU 3 subjects + TruthfulQA 3 categories + GSM8K 100 problems):

- Per model: 20-40 minutes
- 3 models total: 1-2 hours

To reduce time, decrease the number of subjects in `MMLU_TASKS`, reduce categories in `TRUTHFULQA_TASKS`, or make `GSM8K_N_PROBLEMS` smaller in `.env`.

## Memory Usage

Ollama loads models one at a time into memory and automatically unloads them when switching to another model. LM Studio similarly only consumes memory for the currently loaded model. Works fine with 24GB unified memory (using at most about 10GB for the Q8_0 version).

## License

MIT