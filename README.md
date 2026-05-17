# Budget-Constrained Faithful Summarization

This repository contains experiment code, run scripts, and compact result
evidence for budget-constrained faithful summarization.

The implementation decouples generation from selection:

1. A generation model creates one or more candidate summaries.
2. Candidate summaries are split into sentence candidates and deduplicated.
3. Candidate utility combines semantic coverage and factuality signals.
4. Pairwise redundancy is estimated between candidate sentences.
5. MMR, ILP, or DPP-style greedy selection chooses a budgeted sentence set.
6. Selected sentences are ordered by source similarity and evaluated.

The repository is structured for ongoing experiments. New runs can be added to
`results/raw/` or `results/auxiliary/`, then selected into
`results/tables/current_metrics.csv` through the configurable row list.

## Layout

- `src/`: model-specific runners for BART, PRIMERA, Llama, Qwen, and Gemma.
- `scripts/`: common run, logging, validation, and metric collection scripts.
- `scripts/current_runs/`: commands for the currently selected result set.
- `results/raw/`: compact result evidence used by the current table.
- `results/auxiliary/`: useful run outputs not selected into the current table.
- `results/tables/selected_rows.csv`: configurable list of selected result files.
- `results/tables/current_metrics.csv`: generated metric table.
- `results/tables/missing_or_pending.csv`: known incomplete or unavailable items.
- `docs/`: neutral run notes, dependency notes, and result inventory.

Large model weights, dataset caches, full generation traces, local virtual
environments, and full output trees are intentionally excluded.

## Install

```bash
cd /path/to/budget-constrained-faithful-summarization
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Optional metric assets are resolved with `NLM_ASSETS_DIR` or an untracked
`src/.nlm_assets.json`. See `docs/dependency_notes.md`.

## Run

Use `--num-samples 0` for a full test split. For a quick smoke run, omit it or
set a small number.

```bash
PYTHON=python3 \
  scripts/run_live.sh --name bart_cnn_smoke -- \
  bash scripts/run_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 2
```

To launch the currently selected run set:

```bash
PYTHON=python3 \
  bash scripts/current_runs/run_current_results.sh
```

## Update The Current Table

Add a compact `*_results.txt` file under `results/raw/`, then add its relative
path to `results/tables/selected_rows.csv`.

Regenerate the table:

```bash
python3 scripts/collect_current_metrics.py
```

The generated file is `results/tables/current_metrics.csv`.

## Validate

```bash
bash scripts/validate_static.sh
python3 scripts/collect_current_metrics.py
```

Before pushing, check that tracked content remains neutral with the repository
audit command described in `docs/runbook.md`.
