#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="$ROOT/.venv/bin/python"

export BART_COMPUTE_DTYPE="${BART_COMPUTE_DTYPE:-bf16}"
export BART_GENERATION_BATCH_SIZE="${BART_GENERATION_BATCH_SIZE:-24}"
export BART_UTILITY_BATCH_SIZE="${BART_UTILITY_BATCH_SIZE:-128}"
export BART_EVAL_BATCH_SIZE="${BART_EVAL_BATCH_SIZE:-64}"

echo "=== GB10 runtime ==="
echo "BART_COMPUTE_DTYPE=$BART_COMPUTE_DTYPE"
echo "BART_GENERATION_BATCH_SIZE=$BART_GENERATION_BATCH_SIZE"
echo "BART_UTILITY_BATCH_SIZE=$BART_UTILITY_BATCH_SIZE"
echo "BART_EVAL_BATCH_SIZE=$BART_EVAL_BATCH_SIZE"

exec "$PYTHON" "$ROOT/bart/run.py" \
  --compute-dtype "$BART_COMPUTE_DTYPE" \
  --generation-batch-size "$BART_GENERATION_BATCH_SIZE" \
  --utility-batch-size "$BART_UTILITY_BATCH_SIZE" \
  --eval-batch-size "$BART_EVAL_BATCH_SIZE" \
  "$@"
