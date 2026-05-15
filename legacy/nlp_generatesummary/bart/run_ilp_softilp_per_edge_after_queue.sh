#!/usr/bin/env bash
# Queued full-test run for soft-ILP (tri-metric, per_edge) using the best
# weights validated locally: (w_rouge, w_minicheck, w_redundancy) = (0.10, 0.20, 0.70).
#
# Alignment with the rest of run_chain_20260416.sh:
#   - num_samples=-1 (full CNN/DailyMail test, 11490)
#   - no-resume (fresh start)
#   - BEAM_SIZE from config (=10), BUDGET_SENTENCES (=4)
#   - HF ROUGE, shuffle+seed=42 (defaults)
# Divergences from the chain's original ilp step:
#   - Explicit tri-metric weights overriding TRI_METRIC_WEIGHTS_BY_METHOD
#   - --ilp-penalty-scale per_edge (default, written explicitly for log hygiene)
#   - Separate --output-dir so the pre-existing chain ILP results are NOT overwritten
#
# Ordering: waits for BOTH the chain (PID 1853441) and the baseline_raw beam4
# waiter (PID 1974068) to exit before starting.

set -u
cd /path/to/NLP_generatesummary/bart

PY=/path/to/NLP_generatesummary/.venv/bin/python
STAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR=results/ilp_tri_metric_softilp_per_edge_wr010_wm020_wd070
LOG=results/run_ilp_softilp_per_edge_${STAMP}.log

WAIT_CHAIN_PID=${WAIT_CHAIN_PID:-1853441}
WAIT_BASELINE_PID=${WAIT_BASELINE_PID:-1974068}

mkdir -p "${OUT_DIR}"
echo "=== queued soft-ILP per_edge full-test run ===" | tee -a "${LOG}"
echo "[$(date)] stamp=${STAMP}" | tee -a "${LOG}"
echo "[$(date)] output dir: ${OUT_DIR}" | tee -a "${LOG}"
echo "[$(date)] waiting for chain PID=${WAIT_CHAIN_PID} ..." | tee -a "${LOG}"
while kill -0 "${WAIT_CHAIN_PID}" 2>/dev/null; do sleep 60; done
echo "[$(date)] chain PID=${WAIT_CHAIN_PID} exited." | tee -a "${LOG}"

echo "[$(date)] waiting for baseline_raw rerun PID=${WAIT_BASELINE_PID} ..." | tee -a "${LOG}"
while kill -0 "${WAIT_BASELINE_PID}" 2>/dev/null; do sleep 60; done
echo "[$(date)] baseline_raw rerun PID=${WAIT_BASELINE_PID} exited." | tee -a "${LOG}"

echo "[$(date)] starting soft-ILP full test" | tee -a "${LOG}"

"${PY}" run.py \
  --method ilp --tri-metric \
  --w-rouge 0.10 --w-minicheck 0.20 --w-redundancy 0.70 \
  --ilp-penalty-scale per_edge \
  --num-samples -1 --no-resume \
  --output-dir "${OUT_DIR}" 2>&1 | tee -a "${LOG}"

rc=${PIPESTATUS[0]}
echo "[$(date)] soft-ILP full test finished rc=${rc} log=${LOG}" | tee -a "${LOG}"
exit "${rc}"
