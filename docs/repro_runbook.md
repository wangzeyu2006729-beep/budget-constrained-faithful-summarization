# Reproduction Runbook

All commands below stream logs in real time and save the same output under
`logs/`.

## Validate The Release

```bash
cd /path/to/NLP_acl_repro_release

PYTHON=python3 \
  scripts/run_live.sh --name validate_release -- \
  bash scripts/validate_release_static.sh
```

## Regenerate Compact Result Table

```bash
cd /path/to/NLP_acl_repro_release

scripts/run_live.sh --name collect_paper_metrics -- \
  python3 scripts/collect_paper_metrics.py
```

The output is `results/paper_metrics.csv`.

## Smoke Runs

BART direct baseline on CNN/DailyMail:

```bash
cd /path/to/NLP_acl_repro_release

PYTHON=python3 \
  scripts/run_live.sh --name smoke_bart_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 2 \
    --beam-size 4 \
    --output-tag smoke_bart_baseline
```

PRIMERA plus MMR on Multi-News:

```bash
cd /path/to/NLP_acl_repro_release

PYTHON=python3 \
  scripts/run_live.sh --name smoke_primera_mmr -- \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method mmr \
    --dataset multi_news \
    --num-samples 2 \
    --beam-size 8 \
    --budget-sentences 8 \
    --output-tag smoke_primera_mmr
```

## Full Reproduction Examples

Set `--num-samples 0` for the full split.

CNN/DailyMail Llama baseline:

```bash
cd /path/to/NLP_acl_repro_release

PYTHON=python3 \
  scripts/run_live.sh --name full_llama_cnn_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --output-tag full_llama_cnn_baseline
```

CNN/DailyMail Llama CO selectors:

```bash
cd /path/to/NLP_acl_repro_release

PYTHON=python3 \
  scripts/run_live.sh --name full_llama_cnn_ilp -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method ilp \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 4 \
    --output-tag full_llama_cnn_ilp

PYTHON=python3 \
  scripts/run_live.sh --name full_llama_cnn_dpp -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method dpp \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 4 \
    --output-tag full_llama_cnn_dpp

PYTHON=python3 \
  scripts/run_live.sh --name full_llama_cnn_mmr -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method mmr \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 4 \
    --output-tag full_llama_cnn_mmr
```

Multi-News PRIMERA baseline and CO selectors:

```bash
cd /path/to/NLP_acl_repro_release

PYTHON=python3 \
  scripts/run_live.sh --name full_primera_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method baseline \
    --dataset multi_news \
    --num-samples 0 \
    --beam-size 5 \
    --output-tag full_primera_baseline

for method in ilp dpp mmr; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_primera_${method}" -- \
    bash scripts/run_release_experiment.sh \
      --model primera_multinews \
      --method "$method" \
      --dataset multi_news \
      --num-samples 0 \
      --beam-size 8 \
      --budget-sentences 8 \
      --output-tag "full_primera_${method}"
done
```

## Pending Result

As of May 14, 2026 23:29 EDT, the Llama Multi-News direct baseline has a final
`*_results.txt` and is copied into `results/raw/`. The Llama Multi-News CO
selector run is still pending; do not report Llama+ILP/MMR/DPP Multi-News rows
until final selector result files exist.
