#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

BEAM_SIZE="${BEAM_SIZE:-10}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-fp32}"
NUM_SAMPLES="${NUM_SAMPLES:-11490}"
SAMPLE_MODE="${SAMPLE_MODE:-shuffle}"
SAMPLE_SEED="${SAMPLE_SEED:-42}"

echo "=== BASELINE_RAW Full-Fact Regeneration ==="
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "SAMPLE_MODE=$SAMPLE_MODE SAMPLE_SEED=$SAMPLE_SEED"
echo "Note: NO --rouge-only-eval -> FactCC / MiniCheck will be computed."

"$PYTHON" "$ROOT/bart/run.py" \
  --method baseline_raw \
  --split test \
  --num-samples "$NUM_SAMPLES" \
  --sample-mode "$SAMPLE_MODE" \
  --sample-seed "$SAMPLE_SEED" \
  --beam-size "$BEAM_SIZE" \
  --compute-dtype "$COMPUTE_DTYPE"

echo "Done."
