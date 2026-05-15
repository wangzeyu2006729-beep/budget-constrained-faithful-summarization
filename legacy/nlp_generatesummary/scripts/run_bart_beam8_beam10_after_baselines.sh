#!/usr/bin/env bash
# Queue BART main full-test experiments after the current baseline queue.
# Scope:
#   beam8 and beam10
#   MMR uses the existing beam10 setting: tri-metric 0.0/0.5/0.5
#   ILP uses the existing beam10 soft setting: soft-ILP per_edge 0.10/0.20/0.70
#   LNS uses the existing beam10 soft setting: soft-LNS per_edge 0.10/0.20/0.70
#   DPP uses the existing beam10 setting: minicheck_redundancy objective
set -uo pipefail

ROOT="${ROOT:-/path/to/NLP_generatesummary}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
WAIT_SESSION="${WAIT_SESSION:-remaining_after_r1_queue_20260423_164907}"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${LOG_DIR:-$ROOT/bart/results}"
LOG="$LOG_DIR/run_bart_beam8_beam10_after_baselines_${TS}.log"
mkdir -p "$LOG_DIR"

exec > >(tee -a "$LOG") 2>&1

export PYTHONUNBUFFERED=1
export HF_HOME="${HF_HOME:-/path/to/NLM_data/hf_cache}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-$HF_HOME}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-0}"
SAMPLE_MODE="${SAMPLE_MODE:-shuffle}"
SAMPLE_SEED="${SAMPLE_SEED:-42}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
GENERATION_BATCH_SIZE="${GENERATION_BATCH_SIZE:-}"
UTILITY_BATCH_SIZE="${UTILITY_BATCH_SIZE:-}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-}"

MMR_W_ROUGE="${MMR_W_ROUGE:-0.0}"
MMR_W_MINICHECK="${MMR_W_MINICHECK:-0.5}"
MMR_W_REDUNDANCY="${MMR_W_REDUNDANCY:-0.5}"
SOFT_W_ROUGE="${SOFT_W_ROUGE:-0.10}"
SOFT_W_MINICHECK="${SOFT_W_MINICHECK:-0.20}"
SOFT_W_REDUNDANCY="${SOFT_W_REDUNDANCY:-0.70}"

declare -a BEAMS=(8 10)
declare -a METHODS=(mmr ilp lns dpp)
declare -A STATUS=()

run_method() {
  local beam="$1"
  local method="$2"
  local output_dir=""
  local started_epoch
  local finished_epoch
  local elapsed
  local -a cmd=(
    "$PYTHON" -u "$ROOT/bart/run.py"
    --method "$method"
    --split "$SPLIT"
    --num-samples "$NUM_SAMPLES"
    --sample-mode "$SAMPLE_MODE"
    --sample-seed "$SAMPLE_SEED"
    --beam-size "$beam"
    --compute-dtype "$COMPUTE_DTYPE"
  )

  if [[ -n "$GENERATION_BATCH_SIZE" ]]; then
    cmd+=(--generation-batch-size "$GENERATION_BATCH_SIZE")
  fi
  if [[ -n "$UTILITY_BATCH_SIZE" ]]; then
    cmd+=(--utility-batch-size "$UTILITY_BATCH_SIZE")
  fi
  if [[ -n "$EVAL_BATCH_SIZE" ]]; then
    cmd+=(--eval-batch-size "$EVAL_BATCH_SIZE")
  fi

  case "$method" in
    mmr)
      output_dir="$ROOT/bart/results/mmr_tri_metric"
      cmd+=(
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$MMR_W_ROUGE"
        --w-minicheck "$MMR_W_MINICHECK"
        --w-redundancy "$MMR_W_REDUNDANCY"
      )
      ;;
    ilp)
      output_dir="$ROOT/bart/results/ilp_tri_metric_softilp_per_edge_wr010_wm020_wd070"
      cmd+=(
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$SOFT_W_ROUGE"
        --w-minicheck "$SOFT_W_MINICHECK"
        --w-redundancy "$SOFT_W_REDUNDANCY"
        --ilp-penalty-scale per_edge
      )
      ;;
    lns)
      output_dir="$ROOT/bart/results/lns_tri_metric_softlns_per_edge_wr010_wm020_wd070"
      cmd+=(
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$SOFT_W_ROUGE"
        --w-minicheck "$SOFT_W_MINICHECK"
        --w-redundancy "$SOFT_W_REDUNDANCY"
        --lns-penalty-scale per_edge
      )
      ;;
    dpp)
      output_dir="$ROOT/bart/results/dpp_minicheck_redundancy"
      cmd+=(
        --objective minicheck_redundancy
      )
      ;;
    *)
      echo "[error] unsupported method: $method"
      return 2
      ;;
  esac

  mkdir -p "$output_dir"
  started_epoch="$(date +%s)"
  echo ""
  echo "================================================================"
  echo " [beam${beam} ${method}] started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo " Output dir: $output_dir"
  printf ' Command:'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  echo "================================================================"

  set +e
  stdbuf -oL -eL "${cmd[@]}"
  local rc=$?
  set -u

  STATUS["beam${beam}_${method}"]="$rc"
  finished_epoch="$(date +%s)"
  elapsed=$((finished_epoch - started_epoch))
  echo " [beam${beam} ${method}] finished rc=$rc at $(date '+%Y-%m-%d %H:%M:%S %Z') elapsed=${elapsed}s"
  return 0
}

echo "================================================================"
echo " BART Beam8 + Beam10 Main Full-Test Queue"
echo " Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo " Log: $LOG"
echo " Wait session: $WAIT_SESSION"
echo " Methods: ${METHODS[*]}"
echo " Beams: ${BEAMS[*]}"
echo " Split: $SPLIT"
echo " Num samples: $NUM_SAMPLES (0 means full split)"
echo " Sample mode: $SAMPLE_MODE"
echo " Sample seed: $SAMPLE_SEED"
echo " Compute dtype: $COMPUTE_DTYPE"
echo " MMR tri weights: $MMR_W_ROUGE/$MMR_W_MINICHECK/$MMR_W_REDUNDANCY"
echo " ILP soft per_edge weights: $SOFT_W_ROUGE/$SOFT_W_MINICHECK/$SOFT_W_REDUNDANCY"
echo " LNS soft per_edge weights: $SOFT_W_ROUGE/$SOFT_W_MINICHECK/$SOFT_W_REDUNDANCY"
echo " DPP objective: minicheck_redundancy"
echo " HF_HOME: $HF_HOME"
echo " HF_HUB_OFFLINE: $HF_HUB_OFFLINE"
echo " TRANSFORMERS_OFFLINE: $TRANSFORMERS_OFFLINE"
echo " HF_DATASETS_OFFLINE: $HF_DATASETS_OFFLINE"
echo " CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo "================================================================"

if tmux has-session -t "$WAIT_SESSION" 2>/dev/null; then
  echo "[wait] Baseline queue is still running in tmux session '$WAIT_SESSION'."
  while tmux has-session -t "$WAIT_SESSION" 2>/dev/null; do
    echo "[wait] $(date '+%Y-%m-%d %H:%M:%S %Z') still waiting for $WAIT_SESSION ..."
    sleep 60
  done
  echo "[wait] $WAIT_SESSION finished at $(date '+%Y-%m-%d %H:%M:%S %Z')"
  sleep 10
else
  echo "[wait] No tmux session named '$WAIT_SESSION'; starting BART queue immediately."
fi

cd "$ROOT" || exit 1

for beam in "${BEAMS[@]}"; do
  for method in "${METHODS[@]}"; do
    run_method "$beam" "$method"
    sleep 5
  done
done

echo ""
echo "================================================================"
echo " BART Beam8 + Beam10 Main Full-Test Queue Completed"
echo " Finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
for beam in "${BEAMS[@]}"; do
  for method in "${METHODS[@]}"; do
    key="beam${beam}_${method}"
    echo " $key rc=${STATUS[$key]:-not_run}"
  done
done
echo " Log: $LOG"
echo "================================================================"

for rc in "${STATUS[@]}"; do
  if [[ "$rc" != "0" ]]; then
    exit 1
  fi
done
