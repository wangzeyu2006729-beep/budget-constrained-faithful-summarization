#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
WATCH_SESSION="${WATCH_SESSION:-baseline_raw_fullfact}"

echo "[queue] waiting for tmux session '$WATCH_SESSION' to exit..."
until ! tmux has-session -t "$WATCH_SESSION" 2>/dev/null; do
  sleep 60
done

echo "[queue] '$WATCH_SESSION' finished at $(date '+%F %T'). Launching extra sweeps."
bash "$ROOT/scripts/run_extra_weight_sweeps.sh"
