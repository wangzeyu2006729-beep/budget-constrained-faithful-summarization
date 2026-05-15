#!/usr/bin/env bash
# Queued rerun of baseline_raw with beam=4 (aligned with official HF BART config).
# Waits for the currently running chain (PID passed as $1, default 1853441) to
# finish, then runs baseline_raw with the project's standard full-test flags.
# beam_size is enforced to 4 by core/orchestration.py regardless of --beam-size.

set -u
cd /path/to/NLP_generatesummary/bart

PY=/path/to/NLP_generatesummary/.venv/bin/python
WAIT_PID=${1:-1853441}
STAMP=$(date +%Y%m%d_%H%M%S)
LOG=results/run_baseline_raw_beam4_rerun_${STAMP}.log

echo "=== queued baseline_raw beam4 rerun ===" | tee -a "${LOG}"
echo "[$(date)] waiting for chain PID=${WAIT_PID} to exit..." | tee -a "${LOG}"

while kill -0 "${WAIT_PID}" 2>/dev/null; do
  sleep 60
done

echo "[$(date)] chain PID=${WAIT_PID} exited; starting baseline_raw rerun" | tee -a "${LOG}"

"${PY}" run.py --method baseline_raw --num-samples -1 --no-resume 2>&1 | tee -a "${LOG}"
rc=${PIPESTATUS[0]}

echo "[$(date)] baseline_raw rerun finished rc=${rc} log=${LOG}" | tee -a "${LOG}"
exit "${rc}"
