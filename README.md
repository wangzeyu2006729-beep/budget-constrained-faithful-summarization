````markdown
# Budget-Constrained Faithful Summarization

This repository contains experiment code, run scripts, and compact result evidence for **budget-constrained faithful summarization**.

The main idea is to decouple **generation** from **selection**. Instead of using a single generated summary directly, the system first generates multiple candidate summaries, decomposes them into sentence-level candidates, scores each sentence for coverage and factuality, penalizes redundancy, and then selects a budgeted set of final sentences using optimization-based methods.

## Overview

The pipeline follows a generate-then-select framework:

```text
Input document(s)
    ↓
Generation model produces multiple candidate summaries
    ↓
Candidate summaries are split into sentence candidates
    ↓
Duplicate candidate sentences are removed
    ↓
Each candidate sentence is scored by:
    - source coverage
    - factuality
    - pairwise redundancy
    ↓
A selector chooses a budgeted sentence set:
    - MMR
    - ILP
    - DPP-inspired greedy selection
    ↓
Selected sentences are ordered by source similarity
    ↓
Final summary
    ↓
Evaluation
````

This repository is organized as a **multi-model experiment pipeline**. Each model has its own runner under `src/`, while shared experiment launching, logging, validation, and result collection are handled by `scripts/`.

## Repository Layout

```text
budget-constrained-faithful-summarization/
│
├── scripts/
│   ├── run_experiment.sh
│   ├── run_live.sh
│   ├── collect_current_metrics.py
│   ├── validate_static.sh
│   └── current_runs/
│
├── src/
│   ├── bart/
│   ├── primera_multinews/
│   ├── qwen3_5_9b/
│   ├── llama3_8b/
│   └── gemma4_e4b/
│
├── results/
│   ├── raw/
│   ├── auxiliary/
│   └── tables/
│       ├── selected_rows.csv
│       ├── current_metrics.csv
│       └── missing_or_pending.csv
│
├── docs/
├── requirements.txt
└── README.md
```

### Main directories

| Path                                    | Purpose                                                                                   |
| --------------------------------------- | ----------------------------------------------------------------------------------------- |
| `src/`                                  | Model-specific experiment code.                                                           |
| `src/bart/`                             | BART experiments on CNN/DailyMail.                                                        |
| `src/primera_multinews/`                | PRIMERA experiments on Multi-News.                                                        |
| `src/qwen3_5_9b/`                       | Qwen instruction-tuned generation experiments.                                            |
| `src/llama3_8b/`                        | Llama instruction-tuned generation and selected optimization experiments.                 |
| `src/gemma4_e4b/`                       | Gemma instruction-tuned generation experiments.                                           |
| `scripts/`                              | Common experiment launchers, logging wrappers, validators, and metric collection scripts. |
| `scripts/current_runs/`                 | Commands for the currently selected experiment set.                                       |
| `results/raw/`                          | Compact result evidence used by the current result table.                                 |
| `results/auxiliary/`                    | Auxiliary runs, ablations, or useful outputs not selected into the main table.            |
| `results/tables/selected_rows.csv`      | Configurable list of result files selected for the current table.                         |
| `results/tables/current_metrics.csv`    | Generated metric table.                                                                   |
| `results/tables/missing_or_pending.csv` | Known incomplete, unavailable, or pending items.                                          |
| `docs/`                                 | Run notes, dependency notes, result inventory, and maintenance notes.                     |

Large model weights, dataset caches, full generation traces, local virtual environments, and full output trees are intentionally excluded from version control.

## Code Architecture

The code is organized by model. Each model directory contains a self-contained experiment runner. The BART pipeline is the clearest reference implementation.

### BART pipeline structure

```text
src/bart/
├── run.py
├── cli/
│   └── args.py
├── core/
│   ├── config.py
│   ├── data.py
│   ├── beam_search.py
│   ├── features.py
│   └── orchestration.py
├── opt_selectors/
│   ├── __init__.py
│   ├── tri_metric.py
│   └── sentence_level/
│       ├── mmr.py
│       ├── ilp.py
│       └── dpp.py
├── metrics/
│   ├── evaluation.py
│   ├── factcc_eval_utils.py
│   ├── minicheck_eval_utils.py
│   ├── alignscore_eval_utils.py
│   ├── factkb_eval_utils.py
│   └── factgraph_eval_utils.py
└── output/
    └── result_saver.py
```

### BART execution flow

```text
scripts/run_experiment.sh
        ↓
src/bart/run.py
        ↓
src/bart/cli/args.py
        ↓
src/bart/core/orchestration.py
        ↓
 ┌─────────────────────────────────────────────┐
 │ 1. data.py                                  │
 │    Load CNN/DailyMail                       │
 │                                             │
 │ 2. beam_search.py                           │
 │    Generate candidate summaries             │
 │                                             │
 │ 3. features.py                              │
 │    Build sentence pool                      │
 │    Compute coverage/factuality/redundancy   │
 │                                             │
 │ 4. opt_selectors/                           │
 │    MMR / ILP / DPP select sentences          │
 │                                             │
 │ 5. orchestration.py                         │
 │    Order selected sentences                 │
 │    Build final summary                      │
 │                                             │
 │ 6. metrics/evaluation.py                    │
 │    Evaluate summaries                       │
 │                                             │
 │ 7. output/result_saver.py                   │
 │    Save results                             │
 └─────────────────────────────────────────────┘
        ↓
results/
        ↓
scripts/collect_current_metrics.py
        ↓
results/tables/current_metrics.csv
```

## Main Components

### 1. Candidate Generation

For encoder-decoder models such as BART and PRIMERA, candidate summaries are generated with beam search.

Relevant files:

```text
src/bart/core/beam_search.py
src/primera_multinews/core/beam_search.py
```

For instruction-tuned language models such as Qwen, Llama, and Gemma, candidate summaries are generated through prompt-based generation.

Relevant files:

```text
src/qwen3_5_9b/core/model_generation.py
src/llama3_8b/core/model_generation.py
src/gemma4_e4b/core/model_generation.py
```

### 2. Candidate Pool Construction

Generated summaries are decomposed into sentence-level candidate pools. Exact duplicate sentences are removed. The optimization stage operates on this deduplicated sentence pool.

Relevant files:

```text
src/*/core/features.py
src/*/core/orchestration.py
```

### 3. Feature Scoring

Each candidate sentence receives a utility score based on:

* source coverage
* factuality

In the current implementation, coverage is computed using ROUGE-based overlap, and factuality is estimated with MiniCheck. Pairwise redundancy is computed between candidate sentences, mainly using ROUGE-L-style overlap.

Relevant files:

```text
src/*/core/features.py
src/*/opt_selectors/tri_metric.py
```

### 4. Budgeted Sentence Selection

The repository implements three sentence-level selection methods:

| Method | Description                                                                |
| ------ | -------------------------------------------------------------------------- |
| `MMR`  | Greedy relevance-diversity selection.                                      |
| `ILP`  | Integer linear programming with utility and pairwise redundancy penalty.   |
| `DPP`  | DPP-inspired greedy subset selection using quality and similarity signals. |

Relevant files:

```text
src/*/opt_selectors/sentence_level/mmr.py
src/*/opt_selectors/sentence_level/ilp.py
src/*/opt_selectors/sentence_level/dpp.py
```

The current implementation uses a sentence-count budget. For example, BART experiments on CNN/DailyMail use a sentence budget such as 4 selected sentences, while Multi-News experiments can use a larger sentence budget.

### 5. Summary Realization

The selected sentences are unordered after optimization. The realization step orders selected sentences by source similarity. Each selected sentence is matched to the most similar source sentence, and the final selected sentences are sorted according to the matched source positions.

Relevant file:

```text
src/*/core/orchestration.py
```

### 6. Evaluation

The final summaries are evaluated with generation-quality and faithfulness metrics.

Supported metrics include:

* ROUGE
* BERTScore
* FactCC
* MiniCheck
* AlignScore
* FactKB
* FactGraph

Relevant files:

```text
src/*/metrics/evaluation.py
src/*/metrics/*_eval_utils.py
```

## Installation

```bash
cd /path/to/budget-constrained-faithful-summarization

python3 -m venv .venv
. .venv/bin/activate

pip install -r requirements.txt
```

Some factuality metrics require additional external assets or model checkpoints. Optional metric assets can be resolved with `NLM_ASSETS_DIR` or an untracked `src/.nlm_assets.json`. See `docs/dependency_notes.md` for details.

## Running Experiments

### Smoke run

A small run can be launched through the shared experiment wrapper:

```bash
PYTHON=python3 \
scripts/run_live.sh --name bart_cnn_smoke -- \
bash scripts/run_experiment.sh \
  --model bart \
  --method baseline \
  --dataset cnn_dailymail \
  --num-samples 2
```

### Full BART baseline on CNN/DailyMail

```bash
PYTHON=python3 \
scripts/run_live.sh --name full_bart_cnn_baseline -- \
bash scripts/run_experiment.sh \
  --model bart \
  --method baseline \
  --dataset cnn_dailymail \
  --num-samples 0 \
  --beam-size 4 \
  --output-tag full_bart_cnn_baseline
```

`--num-samples 0` indicates a full test split run in the current experiment scripts.

### BART optimization runs

```bash
PYTHON=python3 \
scripts/run_live.sh --name full_bart_cnn_ilp -- \
bash scripts/run_experiment.sh \
  --model bart \
  --method ilp \
  --dataset cnn_dailymail \
  --num-samples 0 \
  --beam-size 5 \
  --output-tag full_bart_cnn_ilp
```

The `--method` argument can be:

```text
baseline
mmr
ilp
dpp
```

### Current selected run set

To launch the currently selected run set:

```bash
PYTHON=python3 \
bash scripts/current_runs/run_current_results.sh
```

## Result Table Workflow

This repository separates raw experiment evidence from the current reported table.

The workflow is:

```text
new experiment output
    ↓
save compact result file under results/raw/ or results/auxiliary/
    ↓
add selected result path to results/tables/selected_rows.csv
    ↓
run scripts/collect_current_metrics.py
    ↓
generate results/tables/current_metrics.csv
```

To regenerate the current table:

```bash
python3 scripts/collect_current_metrics.py
```

The generated file is:

```text
results/tables/current_metrics.csv
```

Known unavailable or pending items are tracked in:

```text
results/tables/missing_or_pending.csv
```

## Static Validation

Before pushing changes, run:

```bash
bash scripts/validate_static.sh
python3 scripts/collect_current_metrics.py
```

This helps verify that tracked code and table files are internally consistent.

## Alignment Between Code and Paper

The implementation is organized around the following paper-level components:

| Paper component             | Code location                                                                                                         |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Candidate generation        | `src/*/core/beam_search.py` for encoder-decoder models; `src/*/core/model_generation.py` for instruction-tuned models |
| Candidate pool construction | `src/*/core/features.py`, `src/*/core/orchestration.py`                                                               |
| Coverage scoring            | `src/*/core/features.py`                                                                                              |
| Factuality scoring          | `src/*/core/features.py`, `src/*/metrics/minicheck_eval_utils.py`                                                     |
| Redundancy scoring          | `src/*/core/features.py`                                                                                              |
| Budgeted selection          | `src/*/opt_selectors/sentence_level/`                                                                                 |
| Realization ordering        | `src/*/core/orchestration.py`                                                                                         |
| Evaluation                  | `src/*/metrics/evaluation.py`                                                                                         |
| Result saving               | `src/*/output/result_saver.py`                                                                                        |
| Current result table        | `results/tables/selected_rows.csv`, `results/tables/current_metrics.csv`                                              |

## Notes on the Current Implementation

* The current budget is implemented as a **sentence-count budget**, not a strict token-level budget.
* DPP selection is implemented as a **DPP-inspired greedy selector**, not as a probabilistically exact DPP model.
* Coverage and redundancy features are primarily ROUGE-based.
* Factuality utility is based on MiniCheck when available.
* Some external factuality metrics may be unavailable depending on local dependencies and model assets.
* `selected_rows.csv` controls which compact result files are included in the current table.

## Citation

If this repository is used, please cite the corresponding paper or project report:

```bibtex
@misc{wang2026budgetfaithfulsummarization,
  title  = {Decoupling Generation and Selection for Budget-Constrained Faithful Summarization},
  author = {Wang, Zeyu and Wang, Guanghua},
  year   = {2026},
  note   = {Project repository}
}
```

```

```

[1]: https://github.com/wangzeyu2006729-beep/budget-constrained-faithful-summarization "GitHub - wangzeyu2006729-beep/budget-constrained-faithful-summarization · GitHub"
