#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
SESSION_NAME="${SESSION_NAME:-ilp_threshold_sweep}"

exec "$ROOT/scripts/run_persistent.sh" \
  --name "$SESSION_NAME" \
  --workdir "$ROOT" \
  -- \
  bash "$ROOT/scripts/run_ilp_threshold_sweep.sh" "$@"
