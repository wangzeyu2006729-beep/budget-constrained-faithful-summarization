#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
SESSION_NAME="${SESSION_NAME:-tri_dpp_light}"

exec "$ROOT/scripts/run_persistent.sh" \
  --name "$SESSION_NAME" \
  --workdir "$ROOT" \
  -- \
  bash "$ROOT/scripts/run_tri_metric_dpp_light.sh" "$@"
