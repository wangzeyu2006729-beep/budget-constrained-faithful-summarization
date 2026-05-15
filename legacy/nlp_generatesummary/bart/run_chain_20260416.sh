#!/usr/bin/env bash
# Sequential full-test chain: baseline_raw -> ilp -> lns -> mmr -> dpp
# Each method runs with --num-samples -1 and --no-resume (fresh).
# FactGraph is intentionally left as unavailable this round (no conda env).

set -u
cd /path/to/NLP_generatesummary/bart
PY=/path/to/NLP_generatesummary/.venv/bin/python
STAMP=$(date +%Y%m%d_%H%M%S)
MASTER=results/run_chain_${STAMP}.master.log

echo "=== chain started at $(date) (stamp=${STAMP}) ===" | tee -a "${MASTER}"

run_m () {
  local method=$1; shift
  local log="results/run_${method}_${STAMP}.log"
  echo "--- [$(date)] BEGIN ${method} ---" | tee -a "${MASTER}"
  "${PY}" run.py --method "${method}" "$@" --num-samples -1 --no-resume 2>&1 | tee "${log}"
  local rc=${PIPESTATUS[0]}
  echo "--- [$(date)] END   ${method} rc=${rc} log=${log} ---" | tee -a "${MASTER}"
  return 0
}

run_m baseline_raw
run_m ilp --tri-metric
run_m lns --tri-metric
run_m mmr --tri-metric
run_m dpp --objective minicheck_redundancy

echo "=== chain finished at $(date) ===" | tee -a "${MASTER}"
