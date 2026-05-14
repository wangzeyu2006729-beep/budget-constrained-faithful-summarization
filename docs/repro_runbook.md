# Reproduction Runbook

All commands below stream logs in real time and save the same output under
`logs/`.

## Validate The Release

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name validate_release -- \
  bash scripts/validate_release_static.sh
```

## Regenerate Compact Result Table

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

scripts/run_live.sh --name collect_paper_metrics -- \
  python3 scripts/collect_paper_metrics.py
```

The output is `results/paper_metrics.csv`.

## Smoke Runs

BART direct baseline on CNN/DailyMail:

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
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
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
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
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
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
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name full_llama_cnn_ilp -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method ilp \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 4 \
    --output-tag full_llama_cnn_ilp

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name full_llama_cnn_dpp -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method dpp \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 4 \
    --output-tag full_llama_cnn_dpp

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
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
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name full_primera_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method baseline \
    --dataset multi_news \
    --num-samples 0 \
    --beam-size 5 \
    --output-tag full_primera_baseline

for method in ilp dpp mmr; do
  PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
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

As of May 14, 2026, the original Llama Multi-News baseline was still running in
the source experiment directory and only had progress files, not a final
`*_results.txt`. It is intentionally not copied into `results/raw/`.
