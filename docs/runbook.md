# Runbook

## One Run

```bash
PYTHON=python3 \
  scripts/run_live.sh --name example_run -- \
  bash scripts/run_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 2
```

Supported models:

- `bart`
- `primera_multinews`
- `llama3_8b`
- `qwen3_5_9b`
- `gemma4_e4b`

Supported methods:

- `baseline`
- `mmr`
- `ilp`
- `dpp`

## Current Run Set

```bash
PYTHON=python3 \
  bash scripts/current_runs/run_current_results.sh
```

This script launches the runs corresponding to
`results/tables/selected_rows.csv`. It is safe to extend when new result rows
are added.

## Metrics Table

```bash
python3 scripts/collect_current_metrics.py
```

The collector reads `results/tables/selected_rows.csv`, parses compact result
files under `results/raw/`, and writes `results/tables/current_metrics.csv`.
