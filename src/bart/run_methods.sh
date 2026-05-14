#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
DATASET="${DATASET:-cnn_dailymail}"
SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-0}"
SAMPLE_MODE="${SAMPLE_MODE:-shuffle}"
BEAM_SIZE="${BEAM_SIZE:-8}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
METHODS="${METHODS:-dpp mmr ilp}"

for method in $METHODS; do
  case "$method" in
    dpp)
      W_ROUGE="${DPP_W_ROUGE:-0.01}"
      W_MINICHECK="${DPP_W_MINICHECK:-0.495}"
      W_REDUNDANCY="${DPP_W_REDUNDANCY:-0.495}"
      ;;
    mmr)
      W_ROUGE="${MMR_W_ROUGE:-0.01}"
      W_MINICHECK="${MMR_W_MINICHECK:-0.495}"
      W_REDUNDANCY="${MMR_W_REDUNDANCY:-0.495}"
      ;;
    ilp)
      W_ROUGE="${ILP_W_ROUGE:-0.01}"
      W_MINICHECK="${ILP_W_MINICHECK:-0.495}"
      W_REDUNDANCY="${ILP_W_REDUNDANCY:-0.495}"
      ;;
    *)
      echo "Unsupported method: $method" >&2
      exit 2
      ;;
  esac

  # BART-large (~400M) is tiny; beam=8, batch=32 → ~16GB peak, well within limits
  CO_GEN_BATCH="${CO_GENERATION_BATCH_SIZE:-32}"
  TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
  OUTPUT_DIR="$ROOT/outputs/$DATASET/bart/${method}/full_${DATASET}_co_tri_metric_${TIMESTAMP}"
  "$PYTHON" "$SCRIPT_DIR/run.py" \
    --method "$method" \
    --generator bart \
    --dataset "$DATASET" \
    --split "$SPLIT" \
    --num-samples "$NUM_SAMPLES" \
    --sample-mode "$SAMPLE_MODE" \
    --beam-size "$BEAM_SIZE" \
    --generation-batch-size "$CO_GEN_BATCH" \
    --compute-dtype "$COMPUTE_DTYPE" \
    --tri-metric \
    --w-rouge "$W_ROUGE" --w-minicheck "$W_MINICHECK" --w-redundancy "$W_REDUNDANCY" \
    --output-dir "$OUTPUT_DIR"
done
