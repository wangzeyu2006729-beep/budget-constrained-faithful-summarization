#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

SPLIT="${SPLIT:-validation}"
NUM_SAMPLES="${NUM_SAMPLES:-50}"
BEAM_SIZE="${BEAM_SIZE:-10}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
PAPER_METRICS="${PAPER_METRICS:-rouge}"
EXTRA_METRICS="${EXTRA_METRICS:-minicheck factcc}"

WEIGHTS_FILE="${WEIGHTS_FILE:-$ROOT/scripts/tri_metric_dpp_light_weights.csv}"
GRID_CSV="${GRID_CSV:-$ROOT/bart/results/tri_metric_grid_search_dpp_light_${SPLIT}_n${NUM_SAMPLES}.csv}"
GRID_RUN_ROOT="${GRID_RUN_ROOT:-$ROOT/bart/results/tri_metric_grid_runs_dpp_light_${SPLIT}_n${NUM_SAMPLES}}"

read -r -a PAPER_METRIC_ARGS <<< "$PAPER_METRICS"
read -r -a EXTRA_METRIC_ARGS <<< "$EXTRA_METRICS"

echo "=== DPP Tri-Metric Light Sweep ==="
echo "SPLIT=$SPLIT"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "WEIGHTS_FILE=$WEIGHTS_FILE"
echo "PAPER_METRICS=$PAPER_METRICS"
echo "EXTRA_METRICS=$EXTRA_METRICS"
echo "GRID_CSV=$GRID_CSV"
echo "GRID_RUN_ROOT=$GRID_RUN_ROOT"

"$PYTHON" "$ROOT/scripts/run_tri_metric_grid.py" \
  --methods dpp \
  --split "$SPLIT" \
  --num-samples "$NUM_SAMPLES" \
  --beam-size "$BEAM_SIZE" \
  --weights-file "$WEIGHTS_FILE" \
  --compute-dtype "$COMPUTE_DTYPE" \
  --paper-metrics "${PAPER_METRIC_ARGS[@]}" \
  --extra-metrics "${EXTRA_METRIC_ARGS[@]}" \
  --resume \
  --output-csv "$GRID_CSV" \
  --run-root "$GRID_RUN_ROOT"

echo
echo "Grid CSV: $GRID_CSV"
