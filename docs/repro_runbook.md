# Reproduction Runbook

All commands stream logs in real time and save the same output under `logs/`.
The commands below are aligned with the local rows currently filled in the
paper table.

## Validate The Release

```bash
cd /path/to/budget-constrained-faithful-summarization

PYTHON=python3 \
  scripts/run_live.sh --name validate_release -- \
  bash scripts/validate_release_static.sh
```

## Regenerate Compact Result Table

```bash
cd /path/to/budget-constrained-faithful-summarization

scripts/run_live.sh --name collect_paper_metrics -- \
  python3 scripts/collect_paper_metrics.py
```

The output is `results/paper_metrics.csv`. It intentionally excludes
`results/auxiliary/`.

## Full Paper-Reported Local Rows

Run the complete list:

```bash
cd /path/to/budget-constrained-faithful-summarization

PYTHON=python3 \
  bash scripts/paper_runs/run_current_paper_rows.sh
```

BART CNN/DailyMail direct baseline:

```bash
cd /path/to/budget-constrained-faithful-summarization

PYTHON=python3 \
  scripts/run_live.sh --name full_bart_cnn_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 4 \
    --output-tag full_bart_cnn_baseline
```

BART CNN/DailyMail CO selectors:

```bash
cd /path/to/budget-constrained-faithful-summarization

for method in mmr ilp dpp; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_bart_cnn_${method}" -- \
    bash scripts/run_release_experiment.sh \
      --model bart \
      --method "$method" \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --beam-size 5 \
      --output-tag "full_bart_cnn_${method}"
done
```

Instruction-tuned CNN/DailyMail direct baselines:

```bash
cd /path/to/budget-constrained-faithful-summarization

for model in qwen3_5_9b llama3_8b gemma4_e4b; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_${model}_cnn_baseline" -- \
    bash scripts/run_release_experiment.sh \
      --model "$model" \
      --method baseline \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --output-tag "full_${model}_cnn_baseline"
done
```

CNN/DailyMail Llama CO rows:

```bash
cd /path/to/budget-constrained-faithful-summarization

for method in mmr ilp; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_llama_cnn_${method}_new_w" -- \
    bash scripts/run_release_experiment.sh \
      --model llama3_8b \
      --method "$method" \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --beam-size 8 \
      --budget-sentences 4 \
      --output-tag "full_llama_cnn_${method}_new_w" -- \
      --w-rouge 0.20 \
      --w-minicheck 0.60 \
      --w-redundancy 0.20
done

PYTHON=python3 \
  scripts/run_live.sh --name full_llama_cnn_dpp_old_w -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method dpp \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 4 \
    --output-tag full_llama_cnn_dpp_old_w -- \
    --w-rouge 0.01 \
    --w-minicheck 0.495 \
    --w-redundancy 0.495
```

Multi-News PRIMERA baseline and CO selectors:

```bash
cd /path/to/budget-constrained-faithful-summarization

PYTHON=python3 \
  scripts/run_live.sh --name full_primera_multinews_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method baseline \
    --dataset multi_news \
    --num-samples 0 \
    --beam-size 5 \
    --output-tag full_primera_multinews_baseline

for method in mmr ilp dpp; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_primera_multinews_${method}" -- \
    bash scripts/run_release_experiment.sh \
      --model primera_multinews \
      --method "$method" \
      --dataset multi_news \
      --num-samples 0 \
      --beam-size 8 \
      --budget-sentences 8 \
      --output-tag "full_primera_multinews_${method}"
done
```

## Small Static/Dry-Run Checks

These do not load models when `DRY_RUN=1` is set.

```bash
cd /path/to/budget-constrained-faithful-summarization

DRY_RUN=1 PYTHON=python3 \
  scripts/run_live.sh --name dryrun_bart_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 2 \
    --beam-size 4 \
    --output-tag dryrun_bart_baseline
```

## Pending Or Auxiliary Rows

- Multi-News Qwen/Llama/Gemma rows are blank or unavailable in the current
  paper table; completed local artifacts remain auxiliary unless the paper is
  updated.
- The current server job is a Llama Multi-News ILP CO run. It must not be
  reported until a final `*_results.txt` exists and the paper table is updated.
