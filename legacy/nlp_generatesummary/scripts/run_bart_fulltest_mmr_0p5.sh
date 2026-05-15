#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary

EXPLICIT_TRI_METHODS="mmr" \
EXPLICIT_W_ROUGE="0.0" \
EXPLICIT_W_MINICHECK="0.5" \
EXPLICIT_W_REDUNDANCY="0.5" \
NONWEIGHT_METHODS="" \
INCLUDE_PARETO="0" \
INCLUDE_MBR="0" \
INCLUDE_BASELINE_RAW="0" \
exec bash "$ROOT/scripts/run_bart_fulltest_low_tune.sh" "$@"
