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

A command-line tool that evaluates and compares local LLMs running on **Ollama** or **LM Studio** under identical conditions using **deepeval**'s public benchmarks (MMLU, TruthfulQA, GSM8K).

Execute benchmarks in batch for multiple models, display comparison tables in the terminal, and save results in JSON format.

---

## Table of Contents

- [Features](#features)
- [Supported Benchmarks](#supported-benchmarks)
- [Technology Stack](#technology-stack)
- [Requirements](#requirements)
- [Setup](#setup)
- [Environment Variable Configuration](#environment-variable-configuration)
- [Usage](#usage)
- [Output Examples](#output-examples)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Multi-backend Support** — Supports both Ollama and LM Studio, switchable with a single environment variable
- **Three Standard Benchmarks** — Supports MMLU (knowledge), TruthfulQA (fact verification), and GSM8K (mathematical reasoning)
- **Flexible Configuration** — Fine-grained control of subjects, categories, number of problems, few-shot counts, etc., via `.env` file
- **Multi-model Batch Comparison** — Sequentially evaluates multiple models under identical conditions and automatically generates comparison tables
- **Pre-check Functionality** — Automatically verifies server connections and model availability before benchmark execution
- **Result Persistence** — Saves all results (including task-specific scores) to timestamped JSON files
- **Localized CLI Output** — Displays clear comparison tables in the terminal

---

## Supported Benchmarks

| Benchmark | Overview | Evaluation Content |
|---|---|---|
| **MMLU** | Massive Multitask Language Understanding | Knowledge and comprehension across 57 subjects (Few-shot supported) |
| **TruthfulQA** | Truthful Question Answering | Factually accurate response capability (MC1/MC2 modes) |
| **GSM8K** | Grade School Math 8K | Elementary-level math word problems (Chain of Thought supported) |

---

## Technology Stack

| Category | Technology |
|---|---|
| Language | Python 3.12+ |
| Benchmark Framework | deepeval (≥3.8.0) |
| LLM Backend | Ollama (ollama ≥0.4.0) / LM Studio (openai ≥1.0.0) |
| Configuration Management | python-dotenv (≥1.0.0) |
| Table Display | tabulate (≥0.9.0) |

---

## Requirements

- **Python 3.12** or higher
- **Ollama** or **LM Studio** running locally
- Target models must be pre-downloaded and loaded

---

## Setup

### 1. Clone the Repository

```bash
git clone [Insert repository URL here]
cd llm-benchmark-script
```

### 2. Install Dependencies

**Using uv (recommended):**

```bash
uv sync
```

**Using pip:**

```bash
pip install .
```

### 3. Create Environment Variables File

```bash
cp .env.example .env
```

Edit the copied `.env` file and adjust settings according to your backend and models.

### 4. Prepare LLM Backend

**For Ollama:**

```bash
# Start Ollama server
ollama serve

# Download models (example)
ollama pull qwen3:8b
```

**For LM Studio:**

Start LM Studio and launch the local server from the "Developer" tab. Target models must be pre-loaded.

---

## Environment Variable Configuration

All settings are managed through the `.env` file. Below is a list of configuration items.

### Basic Settings

| Environment Variable | Description | Default |
|---|---|---|
| `LLM_BACKEND` | Backend to use (`ollama` or `lmstudio`) | `ollama` |
| `BENCHMARK_MODELS` | Model names to evaluate (comma-separated) | 3 Qwen3.5 models |
| `BENCHMARK_TYPES` | Benchmarks to run (comma-separated) | `MMLU,TruthfulQA,GSM8K` |

### Benchmark Settings

| Environment Variable | Description | Default |
|---|---|---|
| `MMLU_TASKS` | Filter MMLU subjects (empty for all 57 subjects) | 3 subjects |
| `MMLU_N_SHOTS` | MMLU few-shot count (max 5) | `5` |
| `TRUTHFULQA_MODE` | MC1 (single answer) or MC2 (multiple correct) | `MC1` |
| `TRUTHFULQA_TASKS` | Filter TruthfulQA categories (empty for all 38 categories) | 3 categories |
| `GSM8K_N_PROBLEMS` | Number of GSM8K problems to run (0 for all 1319) | `100` |
| `GSM8K_N_SHOTS` | GSM8K few-shot count | `3` |
| `GSM8K_ENABLE_COT` | Enable Chain of Thought | `true` |

### Backend-specific Settings

| Environment Variable | Description | Default |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `LMSTUDIO_BASE_URL` | LM Studio server URL (including /v1) | `http://localhost:1234/v1` |
| `LMSTUDIO_API_KEY` | LM Studio API key (dummy acceptable) | `lm-studio` |

### deepeval Timeout Settings

| Environment Variable | Description | Default |
|---|---|---|
| `DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE` | Maximum wait time per problem (seconds) | `900` |
| `DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE` | Maximum wait time per API call (seconds) | `600` |
| `DEEPEVAL_RETRY_MAX_ATTEMPTS` | Retry count | `2` |

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

---

## Usage

### Basic Execution

```bash
python run_benchmark.py
```

Or, if installed as a package, you can also run with the following command:

```bash
llm-benchmark
```

### Execution Flow

The tool processes in the following order:

1. Load settings from `.env` file and perform validation
2. Verify connection to specified backend (Ollama / LM Studio)
3. Validate existence and load status of each model through test generation
4. Execute all model × all benchmark combinations sequentially
5. Save results to `results/` directory in JSON format
6. Display comparison summary table and task-specific detail tables in terminal

### Interrupting Execution

You can safely interrupt at any time with `Ctrl+C`.

---

## Output Examples

### Terminal Output

```
======================================================================
 Local LLM Benchmark Comparison Tool
======================================================================
 Backend: Ollama
 Target Models: 2
   1. qwen3:8b
   2. qwen3:4b
 Benchmarks: MMLU, TruthfulQA, GSM8K
 Server: http://localhost:11434
======================================================================

======================================================================
 Benchmark Results Comparison (overall_score)
======================================================================
+------------+--------+------------+--------+
| Model      | MMLU   | TruthfulQA | GSM8K  |
+------------+--------+------------+--------+
| qwen3:8b   | 0.7200 | 0.5400     | 0.8100 |
| qwen3:4b   | 0.6500 | 0.4800     | 0.7200 |
+------------+--------+------------+--------+
```

### JSON Output

Results are saved to `results/benchmark_YYYYMMDD_HHMMSS.json`. Includes timestamp, Python version, backend information, overall_score and task-specific scores for each model.

---

## Project Structure

```
llm-benchmark-script/
├── run_benchmark.py     # Main entry point
├── config.py            # Environment variable loading/validation
├── benchmarks.py        # Benchmark generation/execution logic
├── reporting.py         # Result saving/table display
├── models/
│   ├── __init__.py      # Backend routing interface
│   ├── ollama_model.py  # Ollama backend implementation
│   └── lmstudio_model.py  # LM Studio backend implementation
├── results/             # Benchmark results storage (JSON)
│   └── .gitkeep
├── .env.example         # Environment variable template
├── pyproject.toml       # Project settings/dependencies
├── .python-version      # Python version specification
└── .gitignore
```

---

## Troubleshooting

### Cannot Connect to Server

For Ollama, check if the server is running with `ollama serve`. For LM Studio, verify that the local server is started from the "Developer" tab.

### Models Are Skipped

The specified model may not be downloaded or loaded in the backend. For Ollama, check with `ollama list`; for LM Studio, verify model status in the app.

### Timeouts Occur

Local LLMs can take time to respond. Increase the values of `DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE` and `DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE` in `.env`. For 9B-class models, 600-900 seconds is recommended.

### Full Subject/Category Execution Takes Too Long

MMLU has 57 subjects, TruthfulQA has 38 categories (817 questions), and GSM8K has 1319 problems. For initial runs, we recommend filtering with `MMLU_TASKS`, `TRUTHFULQA_TASKS`, and `GSM8K_N_PROBLEMS`.

---

## License

MIT
