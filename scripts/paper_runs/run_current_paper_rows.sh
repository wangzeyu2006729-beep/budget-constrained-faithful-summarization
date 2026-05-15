#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-python3}"

cd "$ROOT"

run_logged() {
  local name="$1"
  shift
  PYTHON="$PYTHON" scripts/run_live.sh --name "$name" -- "$@"
}

run_logged full_bart_cnn_baseline \
  bash scripts/run_release_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 4 \
    --output-tag full_bart_cnn_baseline

for method in mmr ilp dpp; do
  run_logged "full_bart_cnn_${method}" \
    bash scripts/run_release_experiment.sh \
      --model bart \
      --method "$method" \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --beam-size 5 \
      --output-tag "full_bart_cnn_${method}"
done

for model in qwen3_5_9b llama3_8b gemma4_e4b; do
  run_logged "full_${model}_cnn_baseline" \
    bash scripts/run_release_experiment.sh \
      --model "$model" \
      --method baseline \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --output-tag "full_${model}_cnn_baseline"
done

for method in mmr ilp; do
  run_logged "full_llama_cnn_${method}_new_w" \
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

run_logged full_llama_cnn_dpp_old_w \
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

run_logged full_primera_multinews_baseline \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method baseline \
    --dataset multi_news \
    --num-samples 0 \
    --beam-size 5 \
    --output-tag full_primera_multinews_baseline

for method in mmr ilp dpp; do
  run_logged "full_primera_multinews_${method}" \
    bash scripts/run_release_experiment.sh \
      --model primera_multinews \
      --method "$method" \
      --dataset multi_news \
      --num-samples 0 \
      --beam-size 8 \
      --budget-sentences 8 \
      --output-tag "full_primera_multinews_${method}"
done
