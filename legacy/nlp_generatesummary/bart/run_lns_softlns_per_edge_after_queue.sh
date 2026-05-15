#!/usr/bin/env bash
# Queued full-test run for soft-LNS (tri-metric, per_edge) using the best
# weights validated locally: (w_rouge, w_minicheck, w_redundancy) = (0.10, 0.20, 0.70).
#
# Alignment with the rest of run_chain_20260416.sh:
#   - num_samples=-1 (full CNN/DailyMail test, 11490)
#   - no-resume (fresh start)
#   - BEAM_SIZE from config (=10), BUDGET_SENTENCES (=4)
#   - HF ROUGE, shuffle+seed=42 (defaults)
# Divergences from the chain's original lns step (which used old hard repair):
#   - soft-LNS repair under tri-metric (algorithm change in lns.py)
#   - Explicit tri-metric weights overriding TRI_METRIC_WEIGHTS_BY_METHOD
#   - --lns-penalty-scale per_edge (default, written explicitly for log hygiene)
#   - Separate --output-dir so the pre-existing chain LNS results are NOT overwritten
#
# Ordering: waits for the previously-queued soft-ILP waiter (PID 2295683) to
# exit. That waiter itself waits for the chain (1853441) and baseline_raw
# rerun (1974068), so this task runs after all three predecessors finish.

set -u
cd /path/to/NLP_generatesummary/bart

PY=/path/to/NLP_generatesummary/.venv/bin/python
STAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR=results/lns_tri_metric_softlns_per_edge_wr010_wm020_wd070
LOG=results/run_lns_softlns_per_edge_${STAMP}.log

WAIT_ILP_PID=${WAIT_ILP_PID:-2295683}

mkdir -p "${OUT_DIR}"
echo "=== queued soft-LNS per_edge full-test run ===" | tee -a "${LOG}"
echo "[$(date)] stamp=${STAMP}" | tee -a "${LOG}"
echo "[$(date)] output dir: ${OUT_DIR}" | tee -a "${LOG}"
echo "[$(date)] waiting for soft-ILP waiter PID=${WAIT_ILP_PID} ..." | tee -a "${LOG}"
while kill -0 "${WAIT_ILP_PID}" 2>/dev/null; do sleep 60; done
echo "[$(date)] soft-ILP waiter PID=${WAIT_ILP_PID} exited; starting soft-LNS full test" | tee -a "${LOG}"

"${PY}" run.py \
  --method lns --tri-metric \
  --w-rouge 0.10 --w-minicheck 0.20 --w-redundancy 0.70 \
  --lns-penalty-scale per_edge \
  --num-samples -1 --no-resume \
  --output-dir "${OUT_DIR}" 2>&1 | tee -a "${LOG}"

rc=${PIPESTATUS[0]}
echo "[$(date)] soft-LNS full test finished rc=${rc} log=${LOG}" | tee -a "${LOG}"
exit "${rc}"
