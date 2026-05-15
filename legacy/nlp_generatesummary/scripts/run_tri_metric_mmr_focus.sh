#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

SPLIT="${SPLIT:-validation}"
NUM_SAMPLES="${NUM_SAMPLES:-50}"
BEAM_SIZE="${BEAM_SIZE:-10}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
FACT_KEY="${FACT_KEY:-MiniCheck}"
MIN_ROUGE1="${MIN_ROUGE1:-40.50}"
MIN_FACT="${MIN_FACT:-96.50}"
CONSTRAINT_PRIORITY="${CONSTRAINT_PRIORITY:-rouge_then_fact}"
TOP_K="${TOP_K:-1}"
APPLY_ALL="${APPLY_ALL:-0}"
ALL_METHODS="${ALL_METHODS:-mmr ilp lns dpp submodular mbr pareto}"

WEIGHTS_FILE="${WEIGHTS_FILE:-$ROOT/scripts/tri_metric_mmr_focus_weights_step0p1.csv}"
GRID_CSV="${GRID_CSV:-$ROOT/bart/results/tri_metric_grid_search_mmr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}.csv}"
GRID_RUN_ROOT="${GRID_RUN_ROOT:-$ROOT/bart/results/tri_metric_grid_runs_mmr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}}"
SELECTED_WEIGHTS_CSV="${SELECTED_WEIGHTS_CSV:-$ROOT/bart/results/tri_metric_selected_weight_mmr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}.csv}"
APPLY_CSV="${APPLY_CSV:-$ROOT/bart/results/tri_metric_apply_all_mmr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}.csv}"
APPLY_RUN_ROOT="${APPLY_RUN_ROOT:-$ROOT/bart/results/tri_metric_apply_all_runs_mmr_focus_step0p1_${SPLIT}_n${NUM_SAMPLES}}"

read -r -a ALL_METHOD_ARGS <<< "$ALL_METHODS"

echo "=== Focused MMR Tri-Metric Search ==="
echo "SPLIT=$SPLIT"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "WEIGHTS_FILE=$WEIGHTS_FILE"
echo "MIN_ROUGE1=$MIN_ROUGE1"
echo "MIN_FACT=$MIN_FACT"
echo "CONSTRAINT_PRIORITY=$CONSTRAINT_PRIORITY"
echo "TOP_K=$TOP_K"
echo "APPLY_ALL=$APPLY_ALL"
echo "GRID_CSV=$GRID_CSV"
echo "SELECTED_WEIGHTS_CSV=$SELECTED_WEIGHTS_CSV"
if [[ "$APPLY_ALL" == "1" ]]; then
  echo "APPLY_CSV=$APPLY_CSV"
  echo "ALL_METHODS=$ALL_METHODS"
fi

echo
echo "=== [1/2] Run focused MMR grid (resume-safe) ==="
"$PYTHON" "$ROOT/scripts/run_tri_metric_grid.py" \
  --methods mmr \
  --split "$SPLIT" \
  --num-samples "$NUM_SAMPLES" \
  --beam-size "$BEAM_SIZE" \
  --weights-file "$WEIGHTS_FILE" \
  --compute-dtype "$COMPUTE_DTYPE" \
  --paper-metrics rouge \
  --extra-metrics minicheck \
  --resume \
  --output-csv "$GRID_CSV" \
  --run-root "$GRID_RUN_ROOT"

echo
echo "=== [2/2] Pick the best focused MMR weight ==="
"$PYTHON" "$ROOT/scripts/select_tri_metric_weight.py" \
  --input-csv "$GRID_CSV" \
  --output-csv "$SELECTED_WEIGHTS_CSV" \
  --method mmr \
  --split "$SPLIT" \
  --num-samples "$NUM_SAMPLES" \
  --select-by rouge_1 \
  --min-rouge1 "$MIN_ROUGE1" \
  --fact-key "$FACT_KEY" \
  --min-fact "$MIN_FACT" \
  --secondary-key rouge_2 \
  --tertiary-key rouge_l \
  --constraint-priority "$CONSTRAINT_PRIORITY" \
  --top-k "$TOP_K"

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
    --paper-metrics rouge \
    --extra-metrics minicheck \
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
