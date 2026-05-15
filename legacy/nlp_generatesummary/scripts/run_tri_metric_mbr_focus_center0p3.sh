#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary

export WEIGHTS_FILE="${WEIGHTS_FILE:-$ROOT/scripts/tri_metric_mbr_focus_weights_center0p3.csv}"
export GRID_CSV="${GRID_CSV:-$ROOT/bart/results/tri_metric_grid_search_mbr_center0p3_${SPLIT:-validation}_n${NUM_SAMPLES:-50}.csv}"
export GRID_RUN_ROOT="${GRID_RUN_ROOT:-$ROOT/bart/results/tri_metric_grid_runs_mbr_center0p3_${SPLIT:-validation}_n${NUM_SAMPLES:-50}}"
export SELECTED_WEIGHTS_CSV="${SELECTED_WEIGHTS_CSV:-$ROOT/bart/results/tri_metric_selected_weight_mbr_center0p3_${SPLIT:-validation}_n${NUM_SAMPLES:-50}.csv}"
export APPLY_CSV="${APPLY_CSV:-$ROOT/bart/results/tri_metric_apply_all_mbr_center0p3_${SPLIT:-validation}_n${NUM_SAMPLES:-50}.csv}"
export APPLY_RUN_ROOT="${APPLY_RUN_ROOT:-$ROOT/bart/results/tri_metric_apply_all_runs_mbr_center0p3_${SPLIT:-validation}_n${NUM_SAMPLES:-50}}"
export EXTRA_METRICS="${EXTRA_METRICS:-minicheck factcc}"

bash "$ROOT/scripts/run_tri_metric_mbr_focus.sh" "$@"
