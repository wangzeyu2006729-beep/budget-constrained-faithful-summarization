#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

AUTO_PICK_FACT_ANCHOR="${AUTO_PICK_FACT_ANCHOR:-1}"
SUMMARY_CSV="${SUMMARY_CSV:-}"
REP_METHOD="${REP_METHOD:-}"
SPLIT="${SPLIT:-validation}"
NUM_SAMPLES="${NUM_SAMPLES:-20}"
WEIGHT_STEP="${WEIGHT_STEP:-0.1}"
BEAM_SIZE="${BEAM_SIZE:-10}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
PAPER_METRICS="${PAPER_METRICS:-rouge}"
EXTRA_METRICS="${EXTRA_METRICS:-minicheck}"
FACT_KEY="${FACT_KEY:-MiniCheck}"
SELECT_BY="${SELECT_BY:-minicheck}"
MIN_ROUGE1="${MIN_ROUGE1:-}"
MIN_FACT="${MIN_FACT:-}"
SECONDARY_KEY="${SECONDARY_KEY:-rouge_1}"
TERTIARY_KEY="${TERTIARY_KEY:-rouge_2}"
TOP_K="${TOP_K:-3}"
ALL_METHODS="${ALL_METHODS:-mmr ilp lns dpp submodular mbr pareto}"

if [[ -z "$SUMMARY_CSV" ]]; then
  if [[ -f "$ROOT/summary_metrics_beam3_hfrouge.csv" ]]; then
    SUMMARY_CSV="$ROOT/summary_metrics_beam3_hfrouge.csv"
  else
    SUMMARY_CSV="$ROOT/bart/results/summary_metrics_beam5_hfrouge.csv"
  fi
fi

if [[ "$AUTO_PICK_FACT_ANCHOR" == "1" || -z "$REP_METHOD" ]]; then
  eval "$(
    "$PYTHON" "$ROOT/scripts/pick_fact_anchor.py" \
      --input-csv "$SUMMARY_CSV" \
      --fact-key "$FACT_KEY" \
      --split test \
      --prefer-optimizable \
      --format env
  )"
  REP_METHOD="${REP_METHOD:-$SEARCH_ANCHOR_METHOD}"
  if [[ -z "$MIN_ROUGE1" && -n "${SEARCH_ANCHOR_ROUGE1:-}" ]]; then
    MIN_ROUGE1="$SEARCH_ANCHOR_ROUGE1"
  fi
fi

GRID_CSV="${GRID_CSV:-$ROOT/bart/results/tri_metric_grid_search_repr_${REP_METHOD}_${SPLIT}_n${NUM_SAMPLES}.csv}"
GRID_RUN_ROOT="${GRID_RUN_ROOT:-$ROOT/bart/results/tri_metric_grid_runs_repr_${REP_METHOD}_${SPLIT}_n${NUM_SAMPLES}}"
SELECTED_WEIGHTS_CSV="${SELECTED_WEIGHTS_CSV:-$ROOT/bart/results/tri_metric_shortlist_weight_${REP_METHOD}_${SPLIT}_n${NUM_SAMPLES}.csv}"
APPLY_CSV="${APPLY_CSV:-$ROOT/bart/results/tri_metric_apply_all_${REP_METHOD}_${SPLIT}_n${NUM_SAMPLES}.csv}"
APPLY_RUN_ROOT="${APPLY_RUN_ROOT:-$ROOT/bart/results/tri_metric_apply_all_runs_${REP_METHOD}_${SPLIT}_n${NUM_SAMPLES}}"
SHARED_WEIGHTS_CSV="${SHARED_WEIGHTS_CSV:-$ROOT/bart/results/tri_metric_shared_weight_${REP_METHOD}_${SPLIT}_n${NUM_SAMPLES}.csv}"

read -r -a PAPER_METRIC_ARGS <<< "$PAPER_METRICS"
read -r -a EXTRA_METRIC_ARGS <<< "$EXTRA_METRICS"
read -r -a ALL_METHOD_ARGS <<< "$ALL_METHODS"

echo "=== Representative Tri-Metric Workflow ==="
echo "AUTO_PICK_FACT_ANCHOR=$AUTO_PICK_FACT_ANCHOR"
echo "SUMMARY_CSV=$SUMMARY_CSV"
echo "REP_METHOD=$REP_METHOD"
echo "SPLIT=$SPLIT"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "WEIGHT_STEP=$WEIGHT_STEP"
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "PAPER_METRICS=$PAPER_METRICS"
echo "EXTRA_METRICS=$EXTRA_METRICS"
echo "SELECT_BY=$SELECT_BY"
echo "MIN_ROUGE1=$MIN_ROUGE1"
echo "MIN_FACT=$MIN_FACT"
echo "FACT_KEY=$FACT_KEY"
echo "SECONDARY_KEY=$SECONDARY_KEY"
echo "TERTIARY_KEY=$TERTIARY_KEY"
echo "TOP_K=$TOP_K"
echo "ALL_METHODS=$ALL_METHODS"
echo "GRID_CSV=$GRID_CSV"
echo "SHORTLIST_WEIGHTS_CSV=$SELECTED_WEIGHTS_CSV"
echo "APPLY_CSV=$APPLY_CSV"
echo "SHARED_WEIGHTS_CSV=$SHARED_WEIGHTS_CSV"
if [[ -n "${SEARCH_ANCHOR_METHOD:-}" ]]; then
  echo "ANCHOR_METHOD=$SEARCH_ANCHOR_METHOD"
  echo "ANCHOR_OBJECTIVE=${SEARCH_ANCHOR_OBJECTIVE:-}"
  echo "ANCHOR_FACT=${SEARCH_ANCHOR_FACT_SCORE:-}"
  echo "ANCHOR_ROUGE1=${SEARCH_ANCHOR_ROUGE1:-}"
  echo "ANCHOR_WEIGHT_MODE=${SEARCH_ANCHOR_WEIGHT_MODE:-}"
  echo "ANCHOR_HAS_EXPLICIT_WEIGHTS=${SEARCH_ANCHOR_HAS_EXPLICIT_WEIGHTS:-}"
  echo "ANCHOR_WEIGHT_NOTE=${SEARCH_ANCHOR_WEIGHT_NOTE:-}"
fi

echo
echo "=== [1/4] Representative method grid search (resume-safe) ==="
"$PYTHON" "$ROOT/scripts/run_tri_metric_grid.py" \
  --methods "$REP_METHOD" \
  --split "$SPLIT" \
  --num-samples "$NUM_SAMPLES" \
  --beam-size "$BEAM_SIZE" \
  --weight-step "$WEIGHT_STEP" \
  --compute-dtype "$COMPUTE_DTYPE" \
  --paper-metrics "${PAPER_METRIC_ARGS[@]}" \
  --extra-metrics "${EXTRA_METRIC_ARGS[@]}" \
  --resume \
  --output-csv "$GRID_CSV" \
  --run-root "$GRID_RUN_ROOT"

echo
echo "=== [2/4] Select shortlist on the anchor method ==="
SELECT_ARGS=(
  --input-csv "$GRID_CSV"
  --output-csv "$SELECTED_WEIGHTS_CSV"
  --method "$REP_METHOD"
  --split "$SPLIT"
  --num-samples "$NUM_SAMPLES"
  --select-by "$SELECT_BY"
  --fact-key "$FACT_KEY"
  --secondary-key "$SECONDARY_KEY"
  --tertiary-key "$TERTIARY_KEY"
  --top-k "$TOP_K"
)
if [[ -n "$MIN_ROUGE1" ]]; then
  SELECT_ARGS+=(--min-rouge1 "$MIN_ROUGE1")
fi
if [[ -n "$MIN_FACT" ]]; then
  SELECT_ARGS+=(--min-fact "$MIN_FACT")
fi
"$PYTHON" "$ROOT/scripts/select_tri_metric_weight.py" \
  "${SELECT_ARGS[@]}"

echo
echo "=== [3/4] Apply shortlist to all methods (resume-safe) ==="
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

echo
echo "=== [4/4] Pick one shared weight row after cross-method apply ==="
SHARED_SELECT_ARGS=(
  --input-csv "$APPLY_CSV"
  --output-csv "$SHARED_WEIGHTS_CSV"
  --fact-key "$FACT_KEY"
)
if [[ -n "$REP_METHOD" ]]; then
  SHARED_SELECT_ARGS+=(--anchor-method "$REP_METHOD")
fi
if [[ -n "$MIN_ROUGE1" ]]; then
  SHARED_SELECT_ARGS+=(--anchor-rouge1-floor "$MIN_ROUGE1")
fi
"$PYTHON" "$ROOT/scripts/select_shared_tri_metric_weight.py" \
  "${SHARED_SELECT_ARGS[@]}"

echo
echo "Workflow complete."
echo "Representative grid CSV: $GRID_CSV"
echo "Anchor shortlist CSV: $SELECTED_WEIGHTS_CSV"
echo "All-method apply CSV: $APPLY_CSV"
echo "Shared selected weights CSV: $SHARED_WEIGHTS_CSV"
