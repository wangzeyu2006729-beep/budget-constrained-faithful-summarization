#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary

echo "=== Extra Weight Sweeps (MMR focus gap + ILP dense) ==="
echo "Start: $(date '+%F %T')"

echo
echo "--- [1/2] MMR focus gap (2 points) ---"
WEIGHTS_FILE="$ROOT/scripts/tri_metric_mmr_focus_gap_weights.csv" \
GRID_CSV="$ROOT/bart/results/tri_metric_grid_search_mmr_focus_gap_validation_n50.csv" \
GRID_RUN_ROOT="$ROOT/bart/results/tri_metric_grid_runs_mmr_focus_gap_validation_n50" \
bash "$ROOT/scripts/run_tri_metric_mmr_redundancy_10pt.sh"

echo
echo "--- [2/2] ILP dense (10 points) ---"
WEIGHTS_FILE="$ROOT/scripts/tri_metric_ilp_dense_weights.csv" \
GRID_CSV="$ROOT/bart/results/tri_metric_grid_search_ilp_dense_validation_n50.csv" \
GRID_RUN_ROOT="$ROOT/bart/results/tri_metric_grid_runs_ilp_dense_validation_n50" \
bash "$ROOT/scripts/run_tri_metric_ilp_redundancy_10pt.sh"

echo
echo "End: $(date '+%F %T')"
echo "Results:"
echo "  $ROOT/bart/results/tri_metric_grid_search_mmr_focus_gap_validation_n50.csv"
echo "  $ROOT/bart/results/tri_metric_grid_search_ilp_dense_validation_n50.csv"
