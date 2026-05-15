# Reproduction Runbook

All commands stream logs in real time and save the same output under `logs/`.
The commands below are aligned with the local rows currently filled in
`paper/zeyu.tex`.

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

- CNN/DM Llama+MMR/ILP/DPP rows are blank in `zeyu.tex`; related result files
  are kept under `results/auxiliary/not_reported_in_zeyu/`.
- Multi-News rows are blank in `zeyu.tex`; completed PRIMERA/Qwen/Llama/Gemma
  artifacts remain auxiliary and are not parsed into `paper_metrics.csv`.
- The current server job is a Llama Multi-News ILP CO run. It must not be
  reported until a final `*_results.txt` exists and the paper table is updated.
