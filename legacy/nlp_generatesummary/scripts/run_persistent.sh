#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_persistent.sh [--name SESSION_NAME] [--workdir DIR] [--log-dir DIR] -- command [args...]

Examples:
  scripts/run_persistent.sh --name brio -- \
    bash scripts/run_brio_smoke.sh

  scripts/run_persistent.sh --name bart_grid -- \
    bash scripts/run_tri_metric_grid.sh --methods mmr pareto

Behavior:
  - Prefer tmux: starts the job in a detached tmux session so SSH/network drops do not stop it.
  - Fallback to nohup when tmux is unavailable.
  - Always writes a timestamped log file under ~/logs by default.
EOF
}

NAME=""
WORKDIR="$(pwd)"
LOG_DIR="${HOME}/logs"

while [ $# -gt 0 ]; do
  case "$1" in
    --name)
      NAME="${2:?missing value for --name}"
      shift 2
      ;;
    --workdir)
      WORKDIR="${2:?missing value for --workdir}"
      shift 2
      ;;
    --log-dir)
      LOG_DIR="${2:?missing value for --log-dir}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ $# -eq 0 ]; then
  echo "Missing command to run." >&2
  usage >&2
  exit 1
fi

mkdir -p "$LOG_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
if [ -z "$NAME" ]; then
  BASENAME="$(basename "$1")"
  BASENAME="${BASENAME%.*}"
  NAME="${BASENAME}"
fi

SESSION_NAME="$NAME"
LOG_FILE="${LOG_DIR}/${NAME}_${TIMESTAMP}.log"
COMMAND_FILE="${LOG_DIR}/${NAME}_${TIMESTAMP}.command.txt"

printf '%q ' "$@" > "$COMMAND_FILE"
printf '\n' >> "$COMMAND_FILE"

printf -v CMD_STR '%q ' "$@"
if command -v script >/dev/null 2>&1; then
  printf -v RUNNER 'cd %q && echo "[start] $(date -Is)" >> %q && script -qefc %q -a %q; status=$?; echo "[exit] $(date -Is) status=$status" >> %q; exit $status' \
    "$WORKDIR" "$LOG_FILE" "$CMD_STR" "$LOG_FILE" "$LOG_FILE"
else
  printf -v WORKDIR_Q '%q' "$WORKDIR"
  printf -v LOG_Q '%q' "$LOG_FILE"
  RUNNER="cd ${WORKDIR_Q} && echo \"[start] \$(date -Is)\" | tee -a ${LOG_Q} && ${CMD_STR} 2>&1 | tee -a ${LOG_Q}; status=\${PIPESTATUS[0]}; echo \"[exit] \$(date -Is) status=\$status\" | tee -a ${LOG_Q}; exit \$status"
fi

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    SESSION_NAME="${NAME}_${TIMESTAMP}"
  fi

  printf -v TMUX_CMD 'bash -lc %q' "$RUNNER"
  tmux new-session -d -s "$SESSION_NAME" "$TMUX_CMD"

  echo "Started in tmux session: $SESSION_NAME"
  echo "Log file: $LOG_FILE"
  echo "Command file: $COMMAND_FILE"
  echo "Attach: tmux attach -t $SESSION_NAME"
  echo "List sessions: tmux ls"
else
  nohup bash -lc "$RUNNER" >/dev/null 2>&1 < /dev/null &
  PID=$!

  echo "tmux not found, started with nohup."
  echo "PID: $PID"
  echo "Log file: $LOG_FILE"
  echo "Command file: $COMMAND_FILE"
  echo "Check status: ps -fp $PID"
fi
