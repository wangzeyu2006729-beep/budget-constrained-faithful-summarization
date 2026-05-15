#!/usr/bin/env bash
# Full-test timed rerun for Beam-5 selector rows.
# Scope:
#   DPP: MiniCheck + Redundancy
#   MMR: tri-metric 0.0/0.5/0.5
#   ILP: soft per-edge tri-metric 0.10/0.20/0.70
#   LNS: soft per-edge tri-metric 0.10/0.20/0.70

set -uo pipefail

ROOT="${ROOT:-/path/to/NLP_generatesummary}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
TS="${TS:-$(date +%Y%m%d_%H%M%S)}"
LOG_DIR="${LOG_DIR:-$ROOT/bart/results}"
LOG="${LOG:-$LOG_DIR/run_bart_beam5_timed_selectors_${TS}.log}"
BACKUP_DIR="${BACKUP_DIR:-$LOG_DIR/_archive_before_beam5_timed_${TS}}"
LATEST_LOG="$LOG_DIR/run_bart_beam5_timed_selectors_latest.log"
mkdir -p "$LOG_DIR" "$BACKUP_DIR"
ln -sfn "$LOG" "$LATEST_LOG"

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
BEAM="${BEAM:-5}"
NO_RESUME="${NO_RESUME:-1}"

GENERATION_BATCH_SIZE="${GENERATION_BATCH_SIZE:-12}"
UTILITY_BATCH_SIZE="${UTILITY_BATCH_SIZE:-128}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-64}"

MMR_W_ROUGE="${MMR_W_ROUGE:-0.0}"
MMR_W_MINICHECK="${MMR_W_MINICHECK:-0.5}"
MMR_W_REDUNDANCY="${MMR_W_REDUNDANCY:-0.5}"
SOFT_W_ROUGE="${SOFT_W_ROUGE:-0.10}"
SOFT_W_MINICHECK="${SOFT_W_MINICHECK:-0.20}"
SOFT_W_REDUNDANCY="${SOFT_W_REDUNDANCY:-0.70}"

declare -a TASKS=(dpp mmr ilp lns)
declare -A STATUS=()
declare -A ELAPSED=()

backup_if_exists() {
  local path="$1"
  if [[ -e "$path" ]]; then
    local rel="${path#$ROOT/bart/results/}"
    local dst="$BACKUP_DIR/$rel"
    mkdir -p "$(dirname "$dst")"
    cp -p "$path" "$dst"
    echo "[backup] $path -> $dst"
  fi
}

backup_result_family() {
  local result_file="$1"
  backup_if_exists "$result_file"
  backup_if_exists "${result_file/_results.txt/_progress.json}"
  backup_if_exists "${result_file/_results.txt/_progress_summaries.jsonl}"
  backup_if_exists "${result_file/_results.txt/_eval_partial.json}"
  backup_if_exists "${result_file/_results.txt/_results.partial.txt}"
}

add_common_flags() {
  local -n cmd_ref="$1"
  cmd_ref+=(
    --split "$SPLIT"
    --num-samples "$NUM_SAMPLES"
    --sample-mode "$SAMPLE_MODE"
    --sample-seed "$SAMPLE_SEED"
    --beam-size "$BEAM"
    --compute-dtype "$COMPUTE_DTYPE"
    --generation-batch-size "$GENERATION_BATCH_SIZE"
    --utility-batch-size "$UTILITY_BATCH_SIZE"
    --eval-batch-size "$EVAL_BATCH_SIZE"
  )
  if [[ "$NO_RESUME" == "1" ]]; then
    cmd_ref+=(--no-resume)
  fi
}

run_task() {
  local task="$1"
  local output_dir=""
  local result_file=""
  local started_epoch
  local finished_epoch
  local elapsed
  local -a cmd=("$PYTHON" -u "$ROOT/bart/run.py" --method "$task")

  add_common_flags cmd

  case "$task" in
    dpp)
      output_dir="$ROOT/bart/results/dpp_minicheck_redundancy"
      cmd+=(
        --output-dir "$output_dir"
        --objective minicheck_redundancy
      )
      result_file="$output_dir/beam${BEAM}_dpp_minicheck_redundancy_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
      ;;
    mmr)
      output_dir="$ROOT/bart/results/mmr_tri_metric"
      cmd+=(
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$MMR_W_ROUGE"
        --w-minicheck "$MMR_W_MINICHECK"
        --w-redundancy "$MMR_W_REDUNDANCY"
      )
      result_file="$output_dir/beam${BEAM}_mmr_tri_metric_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
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
      result_file="$output_dir/beam${BEAM}_ilp_tri_metric_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
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
      result_file="$output_dir/beam${BEAM}_lns_tri_metric_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
      ;;
    *)
      echo "[error] unsupported task: $task"
      return 2
      ;;
  esac

  mkdir -p "$output_dir"
  backup_result_family "$result_file"

  started_epoch="$(date +%s)"
  echo ""
  echo "================================================================"
  echo " [beam${BEAM} ${task}] started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo " Output dir: $output_dir"
  echo " Expected result: $result_file"
  printf ' Command:'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  echo "================================================================"

  set +e
  stdbuf -oL -eL "${cmd[@]}"
  local rc=$?
  set -u

  finished_epoch="$(date +%s)"
  elapsed=$((finished_epoch - started_epoch))
  STATUS["$task"]="$rc"
  ELAPSED["$task"]="$elapsed"
  echo " [beam${BEAM} ${task}] finished rc=$rc at $(date '+%Y-%m-%d %H:%M:%S %Z') elapsed=${elapsed}s"
  return 0
}

echo "================================================================"
echo " BART Beam-5 timed full-test selector queue"
echo " Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo " Log: $LOG"
echo " Latest log symlink: $LATEST_LOG"
echo " Backup dir: $BACKUP_DIR"
echo " Tasks: ${TASKS[*]}"
echo " Split: $SPLIT"
echo " Num samples: $NUM_SAMPLES (0 means full split)"
echo " Sample mode: $SAMPLE_MODE"
echo " Sample seed: $SAMPLE_SEED"
echo " Beam: $BEAM"
echo " Compute dtype: $COMPUTE_DTYPE"
echo " No resume: $NO_RESUME"
echo " Generation batch size: $GENERATION_BATCH_SIZE"
echo " Utility batch size: $UTILITY_BATCH_SIZE"
echo " Eval batch size: $EVAL_BATCH_SIZE"
echo " MMR tri weights: $MMR_W_ROUGE/$MMR_W_MINICHECK/$MMR_W_REDUNDANCY"
echo " ILP/LNS soft per_edge weights: $SOFT_W_ROUGE/$SOFT_W_MINICHECK/$SOFT_W_REDUNDANCY"
echo " DPP objective: minicheck_redundancy"
echo " HF_HOME: $HF_HOME"
echo " HF_HUB_OFFLINE: $HF_HUB_OFFLINE"
echo " TRANSFORMERS_OFFLINE: $TRANSFORMERS_OFFLINE"
echo " HF_DATASETS_OFFLINE: $HF_DATASETS_OFFLINE"
echo " CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo "================================================================"

cd "$ROOT" || exit 1

for task in "${TASKS[@]}"; do
  run_task "$task"
  sleep 5
done

echo ""
echo "================================================================"
echo " BART Beam-5 timed selector queue completed"
echo " Finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
for task in "${TASKS[@]}"; do
  echo " $task rc=${STATUS[$task]:-not_run} elapsed=${ELAPSED[$task]:-not_run}s"
done
echo " Log: $LOG"
echo " Backup dir: $BACKUP_DIR"
echo "================================================================"

for rc in "${STATUS[@]}"; do
  if [[ "$rc" != "0" ]]; then
    exit 1
  fi
done
