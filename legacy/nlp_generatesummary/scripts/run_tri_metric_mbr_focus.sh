#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

SPLIT="${SPLIT:-validation}"
NUM_SAMPLES="${NUM_SAMPLES:-50}"
BEAM_SIZE="${BEAM_SIZE:-10}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
FACT_KEY="${FACT_KEY:-MiniCheck}"
SELECT_BY="${SELECT_BY:-minicheck}"
MIN_ROUGE1="${MIN_ROUGE1:-}"
MIN_FACT="${MIN_FACT:-}"
CONSTRAINT_PRIORITY="${CONSTRAINT_PRIORITY:-fact_then_rouge}"
SECONDARY_KEY="${SECONDARY_KEY:-rouge_1}"
TERTIARY_KEY="${TERTIARY_KEY:-rouge_2}"
TOP_K="${TOP_K:-1}"
APPLY_ALL="${APPLY_ALL:-0}"
ALL_METHODS="${ALL_METHODS:-mmr ilp lns dpp submodular mbr pareto}"
PAPER_METRICS="${PAPER_METRICS:-rouge}"
EXTRA_METRICS="${EXTRA_METRICS:-minicheck}"

WEIGHTS_FILE="${WEIGHTS_FILE:-$ROOT/scripts/tri_metric_mbr_focus_weights_step0p1.csv}"
GRID_CSV="${GRID_CSV:-$ROOT/bart/results/tri_metric_grid_search_mbr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}.csv}"
GRID_RUN_ROOT="${GRID_RUN_ROOT:-$ROOT/bart/results/tri_metric_grid_runs_mbr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}}"
SELECTED_WEIGHTS_CSV="${SELECTED_WEIGHTS_CSV:-$ROOT/bart/results/tri_metric_selected_weight_mbr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}.csv}"
APPLY_CSV="${APPLY_CSV:-$ROOT/bart/results/tri_metric_apply_all_mbr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}.csv}"
APPLY_RUN_ROOT="${APPLY_RUN_ROOT:-$ROOT/bart/results/tri_metric_apply_all_runs_mbr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}}"

read -r -a ALL_METHOD_ARGS <<< "$ALL_METHODS"
read -r -a PAPER_METRIC_ARGS <<< "$PAPER_METRICS"
read -r -a EXTRA_METRIC_ARGS <<< "$EXTRA_METRICS"

echo "=== Focused MBR Tri-Metric Search ==="
echo "SPLIT=$SPLIT"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "WEIGHTS_FILE=$WEIGHTS_FILE"
echo "SELECT_BY=$SELECT_BY"
echo "MIN_ROUGE1=$MIN_ROUGE1"
echo "MIN_FACT=$MIN_FACT"
echo "CONSTRAINT_PRIORITY=$CONSTRAINT_PRIORITY"
echo "SECONDARY_KEY=$SECONDARY_KEY"
echo "TERTIARY_KEY=$TERTIARY_KEY"
echo "TOP_K=$TOP_K"
echo "APPLY_ALL=$APPLY_ALL"
echo "PAPER_METRICS=$PAPER_METRICS"
echo "EXTRA_METRICS=$EXTRA_METRICS"
echo "GRID_CSV=$GRID_CSV"
echo "SELECTED_WEIGHTS_CSV=$SELECTED_WEIGHTS_CSV"
if [[ "$APPLY_ALL" == "1" ]]; then
  echo "APPLY_CSV=$APPLY_CSV"
  echo "ALL_METHODS=$ALL_METHODS"
fi

echo
echo "=== [1/2] Run focused MBR grid (resume-safe) ==="
"$PYTHON" "$ROOT/scripts/run_tri_metric_grid.py" \
  --methods mbr \
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
echo "=== [2/2] Pick the best focused MBR weight ==="
SELECT_ARGS=(
  --input-csv "$GRID_CSV"
  --output-csv "$SELECTED_WEIGHTS_CSV"
  --method mbr
  --split "$SPLIT"
  --num-samples "$NUM_SAMPLES"
  --select-by "$SELECT_BY"
  --fact-key "$FACT_KEY"
  --secondary-key "$SECONDARY_KEY"
  --tertiary-key "$TERTIARY_KEY"
  --constraint-priority "$CONSTRAINT_PRIORITY"
  --top-k "$TOP_K"
)
if [[ -n "$MIN_ROUGE1" ]]; then
  SELECT_ARGS+=(--min-rouge1 "$MIN_ROUGE1")
fi
if [[ -n "$MIN_FACT" ]]; then
  SELECT_ARGS+=(--min-fact "$MIN_FACT")
fi
"$PYTHON" "$ROOT/scripts/select_tri_metric_weight.py" "${SELECT_ARGS[@]}"

if [[ "$APPLY_ALL" == "1" ]]; then
  echo
  echo "=== [3/3] Apply the selected weight(s) to all methods (resume-safe) ==="
  "$PYTHON" "$ROOT/scripts/run_tri_metric_grid.py" \
    --methods "${ALL_METHOD_ARGS[@]}" \
    --split "$SPLIT" \
    --num-samples "$NUM_SAMPLES" \
    --beam-size "$BEAM_SIZE" \
    --weights-file "$SELECTED_WEIGHTS_CSV" \
    --compute-dtype "$COMPUTE_DTYPE" \
    --paper-metrics "${PAPER_METRIC_ARGS[@]}" \
    --extra-metrics "${EXTRA_METRIC_ARGS[@]}" \
    --resume \
    --output-csv "$APPLY_CSV" \
    --run-root "$APPLY_RUN_ROOT"
fi

echo
echo "Workflow complete."
echo "Grid CSV: $GRID_CSV"
echo "Selected weight CSV: $SELECTED_WEIGHTS_CSV"
if [[ "$APPLY_ALL" == "1" ]]; then
  echo "Apply CSV: $APPLY_CSV"
fi
