# Decoupling Generation and Selection for Budget-Constrained Faithful Summarization

This is the compact reproducibility release for **Decoupling Generation and Selection for Budget-Constrained Faithful Summarization**.

The code follows the paper's final experimental table, not every exploratory run from the original server workspace. The release keeps the runnable source code, the final-table launch scripts, compact result evidence, and table parsing utilities. Large model weights, dataset caches, full logs, and full generation traces are intentionally excluded.

## Start Here

| Need | File |
| --- | --- |
| Run the final selected experiments | `scripts/current_runs/run_current_results.sh` |
| Run one model/method manually | `scripts/run_experiment.sh` |
| Get real-time logs | `scripts/run_live.sh` |
| See final parsed metrics | `results/tables/current_metrics.csv` |
| See selected result files | `results/tables/selected_rows.csv` |
| See unavailable or pending rows | `results/tables/missing_or_pending.csv` |

## Current Final-Table Scope

The committed table currently contains **17 selected rows**.

| Dataset | Included rows |
| --- | --- |
| CNN/DailyMail | BART baseline; BART+MMR/ILP/DPP; Qwen3.5-9B, Llama-3-8B, Gemma-4-E4B baselines; Llama-3-8B+MMR/ILP/DPP. |
| Multi-News | PRIMERA baseline; PRIMERA+MMR/ILP/DPP; Qwen3.5-9B, Llama-3-8B, Gemma-4-E4B baselines. |

Rows that are not in `results/tables/selected_rows.csv` should not be treated as reported paper results. In particular, Multi-News Llama CO rows are pending until completed result files are added and selected.

## Repository Layout

```text
src/                 model-specific runnable code
scripts/             release wrappers and current-run launchers
results/raw/         compact evidence files used by the table
results/tables/      selected rows, parsed metrics, missing/pending notes
docs/                short dependency, runbook, and alignment notes
requirements.txt     core Python dependencies
```

Model entrypoints:

```text
src/bart/run.py
src/primera_multinews/run.py
src/llama3_8b/run.py
src/qwen3_5_9b/run.py
src/gemma4_e4b/run.py
```

The public CLI is kept consistent across model folders:

```text
run.py --method {baseline,mmr,ilp,dpp} --dataset {cnn_dailymail,multi_news}
```

Use `scripts/run_experiment.sh` instead of calling these directly unless you need low-level control.

## Method in This Code

The release implements a generate-then-select summarization pipeline.

1. A backbone model generates candidate summaries.
2. CO runs split generated summaries into sentence candidates and remove exact duplicates.
3. Candidate sentences are scored for coverage and factuality, with pairwise redundancy penalties.
4. `MMR`, `ILP`, or `DPP` selects a sentence subset under a sentence budget.
5. Selected sentences are ordered by source similarity and concatenated.
6. Outputs are evaluated with ROUGE, BERTScore, FactCC, MiniCheck, AlignScore, and FactKB when available.

## Important Claim Boundaries

- The budget used here is a **sentence-count budget**, not a strict token-level budget.
- `DPP` is a **DPP-inspired greedy selector**, not exact probabilistic DPP inference.
- Coverage and redundancy are mainly ROUGE-style lexical overlap signals.
- FactGraph is not reported in the current table because the external evaluator is not configured.
- Some Multi-News LLM baseline MiniCheck values are marked unavailable in the committed evidence; see `results/tables/missing_or_pending.csv`.

## Installation

```bash
git clone https://github.com/wangzeyu2006729-beep/budget-constrained-faithful-summarization.git
cd budget-constrained-faithful-summarization

python3 -m venv .venv
. .venv/bin/activate
mkdir -p logs
PYTHONUNBUFFERED=1 pip install -r requirements.txt 2>&1 | tee logs/install_$(date +%Y%m%d_%H%M%S).log
```

The runners use Hugging Face `datasets` for `cnn_dailymail` and `multi_news`. Optional factuality evaluators may need local model assets; see `docs/dependency_notes.md`.

## Reproduce a Small Run

```bash
PYTHON=python3 scripts/run_live.sh --name smoke_bart_cnn_baseline -- \
  bash scripts/run_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 2
```

## Reproduce the Selected Run Set

This launches the run set corresponding to the rows currently selected for the table.

```bash
PYTHON=python3 scripts/run_live.sh --name current_selected_runs -- \
  bash scripts/current_runs/run_current_results.sh
```

Full runs are expensive and require local GPU/model/dataset cache availability.

## Run One Final-Table Style Experiment

Direct baseline example:

```bash
PYTHON=python3 scripts/run_live.sh --name full_bart_cnn_baseline -- \
  bash scripts/run_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 4 \
    --output-tag full_bart_cnn_baseline
```

CO selection example:

```bash
PYTHON=python3 scripts/run_live.sh --name full_primera_multinews_ilp -- \
  bash scripts/run_experiment.sh \
    --model primera_multinews \
    --method ilp \
    --dataset multi_news \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 8 \
    --output-tag full_primera_multinews_ilp
```

`--num-samples 0` means the full selected split in these scripts.

## Regenerate the Table

Do not edit `results/tables/current_metrics.csv` by hand. It is generated from `selected_rows.csv`.

```bash
PYTHON=python3 scripts/run_live.sh --name collect_current_metrics -- \
  python3 scripts/collect_current_metrics.py
```

Selected compact evidence lives in `results/raw/`. If a new result should become part of the paper table, add its compact result file under `results/raw/`, add a row to `results/tables/selected_rows.csv`, then regenerate `current_metrics.csv`.

## Static Checks

```bash
PYTHON=python3 scripts/run_live.sh --name validate_static -- \
  bash scripts/validate_static.sh
```

This checks shell syntax, Python syntax, and runner `--help` imports. It does not run smoke tests or full experiments.

## Citation

```bibtex
@misc{wang2026budgetfaithfulsummarization,
  title  = {Decoupling Generation and Selection for Budget-Constrained Faithful Summarization},
  author = {Wang, Zeyu and Wang, Guanghua},
  year   = {2026},
  note   = {Reproducibility release}
}
```
