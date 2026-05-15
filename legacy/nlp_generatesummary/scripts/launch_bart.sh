#!/usr/bin/env bash
# launch_bart.sh — one-shot persistent launcher for bart/run.py
#
# Wraps `bart/run.py` in scripts/run_persistent.sh so the job survives SSH/network drops.
# All extra args are forwarded verbatim to run.py.
#
# Examples:
#   scripts/launch_bart.sh --method baseline_raw --num-samples 11490 --beam-size 10
#   scripts/launch_bart.sh --name lns_full --method lns --tri-metric --num-samples 11490
#   BEAM_SIZE=10 scripts/launch_bart.sh --method mmr --tri-metric --num-samples 11490
#
# Survival:
#   - tmux session if tmux is installed (preferred); attach via `tmux attach -t <name>`
#   - nohup fallback otherwise
#   - log under ~/logs/<name>_<timestamp>.log (mirrored from stdout/stderr)
#   - bart/results/run_<method>_<timestamp>.log (Python tee from orchestration.py)
#   - bart/results/<method>_*/<beamN>_<method>_*_eval_partial.json  (incremental eval)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
PERSIST="$SCRIPT_DIR/run_persistent.sh"

NAME=""
PASSTHROUGH=()
while [ $# -gt 0 ]; do
  case "$1" in
    --name)
      NAME="${2:?missing value for --name}"
      shift 2
      ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *)
      PASSTHROUGH+=("$1")
      shift
      ;;
  esac
done

# Auto-name from --method if --name not given
if [ -z "$NAME" ]; then
  for ((i=0; i<${#PASSTHROUGH[@]}; i++)); do
    if [ "${PASSTHROUGH[$i]}" = "--method" ]; then
      NAME="bart_${PASSTHROUGH[$((i+1))]}_$(date +%H%M%S)"
      break
    fi
  done
  NAME="${NAME:-bart_run_$(date +%H%M%S)}"
fi

echo "[launch_bart] session name: $NAME"
echo "[launch_bart] python: $PYTHON"
echo "[launch_bart] forwarding to run.py: ${PASSTHROUGH[*]}"

exec "$PERSIST" --name "$NAME" --workdir "$ROOT" -- \
  "$PYTHON" "$ROOT/bart/run.py" "${PASSTHROUGH[@]}"
