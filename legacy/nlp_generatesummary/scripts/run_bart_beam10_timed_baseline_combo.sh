#!/usr/bin/env bash
# Full-test queue for the paper table timing run:
#   baseline_raw uses the official HF BART beam4 setting.
#   Four combinatorial-optimization methods use beam10.
# The runner prints live logs and records per-method wall-clock elapsed time.

set -uo pipefail

ROOT="${ROOT:-/path/to/NLP_generatesummary}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${LOG_DIR:-$ROOT/bart/results}"
LOG="$LOG_DIR/run_bart_beam10_timed_baseline_combo_${TS}.log"
BACKUP_DIR="$LOG_DIR/_archive_before_beam10_timed_${TS}"
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

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
NO_RESUME="${NO_RESUME:-0}"

BASELINE_BEAM="${BASELINE_BEAM:-4}"
COMBO_BEAM="${COMBO_BEAM:-10}"

MMR_W_ROUGE="${MMR_W_ROUGE:-0.10}"
MMR_W_MINICHECK="${MMR_W_MINICHECK:-0.20}"
MMR_W_REDUNDANCY="${MMR_W_REDUNDANCY:-0.70}"
SOFT_W_ROUGE="${SOFT_W_ROUGE:-0.10}"
SOFT_W_MINICHECK="${SOFT_W_MINICHECK:-0.20}"
SOFT_W_REDUNDANCY="${SOFT_W_REDUNDANCY:-0.70}"
DPP_W_ROUGE="${DPP_W_ROUGE:-0.10}"
DPP_W_MINICHECK="${DPP_W_MINICHECK:-0.45}"
DPP_W_REDUNDANCY="${DPP_W_REDUNDANCY:-0.45}"

if [[ -n "${TASKS_OVERRIDE:-}" ]]; then
  read -r -a TASKS <<< "$TASKS_OVERRIDE"
else
  declare -a TASKS=(baseline_raw mmr ilp lns dpp)
fi
declare -A STATUS=()
declare -A ELAPSED=()

maybe_add_runtime_flags() {
  local -n cmd_ref="$1"
  if [[ -n "$GENERATION_BATCH_SIZE" ]]; then
    cmd_ref+=(--generation-batch-size "$GENERATION_BATCH_SIZE")
  fi
  if [[ -n "$UTILITY_BATCH_SIZE" ]]; then
    cmd_ref+=(--utility-batch-size "$UTILITY_BATCH_SIZE")
  fi
  if [[ -n "$EVAL_BATCH_SIZE" ]]; then
    cmd_ref+=(--eval-batch-size "$EVAL_BATCH_SIZE")
  fi
  if [[ "$NO_RESUME" == "1" ]]; then
    cmd_ref+=(--no-resume)
  fi
}

backup_existing_result() {
  local result_path="$1"
  if [[ -f "$result_path" ]]; then
    local rel="${result_path#$ROOT/bart/results/}"
    local dst="$BACKUP_DIR/$rel"
    mkdir -p "$(dirname "$dst")"
    cp -p "$result_path" "$dst"
    echo "[backup] existing result copied to $dst"
  fi
}

run_task() {
  local task="$1"
  local beam="$COMBO_BEAM"
  local output_dir=""
  local result_file=""
  local started_epoch
  local finished_epoch
  local elapsed
  local -a cmd=(
    "$PYTHON" -u "$ROOT/bart/run.py"
    --method "$task"
    --split "$SPLIT"
    --num-samples "$NUM_SAMPLES"
    --sample-mode "$SAMPLE_MODE"
    --sample-seed "$SAMPLE_SEED"
    --compute-dtype "$COMPUTE_DTYPE"
  )

  case "$task" in
    baseline_raw)
      beam="$BASELINE_BEAM"
      output_dir="$ROOT/bart/results/baseline_raw_baseline_raw"
      cmd+=(--beam-size "$beam" --output-dir "$output_dir")
      result_file="$output_dir/beam${beam}_baseline_raw_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
      ;;
    mmr)
      output_dir="$ROOT/bart/results/mmr_tri_metric_wr010_wm020_wd070"
      cmd+=(
        --beam-size "$beam"
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$MMR_W_ROUGE"
        --w-minicheck "$MMR_W_MINICHECK"
        --w-redundancy "$MMR_W_REDUNDANCY"
      )
      result_file="$output_dir/beam${beam}_mmr_tri_metric_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
      ;;
    ilp)
      output_dir="$ROOT/bart/results/ilp_tri_metric_softilp_per_edge_raw_wr010_wm020_wd070"
      cmd+=(
        --beam-size "$beam"
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$SOFT_W_ROUGE"
        --w-minicheck "$SOFT_W_MINICHECK"
        --w-redundancy "$SOFT_W_REDUNDANCY"
        --ilp-penalty-scale per_edge
      )
      result_file="$output_dir/beam${beam}_ilp_tri_metric_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
      ;;
    lns)
      output_dir="$ROOT/bart/results/lns_tri_metric_softlns_per_edge_raw_wr010_wm020_wd070"
      cmd+=(
        --beam-size "$beam"
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$SOFT_W_ROUGE"
        --w-minicheck "$SOFT_W_MINICHECK"
        --w-redundancy "$SOFT_W_REDUNDANCY"
        --lns-penalty-scale per_edge
      )
      result_file="$output_dir/beam${beam}_lns_tri_metric_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
      ;;
    dpp)
      output_dir="$ROOT/bart/results/dpp_tri_metric_wr010_wm045_wd045"
      cmd+=(
        --beam-size "$beam"
        --output-dir "$output_dir"
        --tri-metric
        --w-rouge "$DPP_W_ROUGE"
        --w-minicheck "$DPP_W_MINICHECK"
        --w-redundancy "$DPP_W_REDUNDANCY"
      )
      result_file="$output_dir/beam${beam}_dpp_tri_metric_hfrouge_${SAMPLE_MODE}_seed${SAMPLE_SEED}_results.txt"
      ;;
    *)
      echo "[error] unsupported task: $task"
      return 2
      ;;
  esac

  maybe_add_runtime_flags cmd
  mkdir -p "$output_dir"
  backup_existing_result "$result_file"

  started_epoch="$(date +%s)"
  echo ""
  echo "================================================================"
  echo " [${task} beam${beam}] started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
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
  echo " [${task} beam${beam}] finished rc=$rc at $(date '+%Y-%m-%d %H:%M:%S %Z') elapsed=${elapsed}s"
  return 0
}

echo "================================================================"
echo " BART Timed Full-Test Queue: baseline_raw beam4 + four beam10 optimizers"
echo " Started: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo " Log: $LOG"
echo " Backup dir: $BACKUP_DIR"
echo " Tasks: ${TASKS[*]}"
echo " Baseline beam: $BASELINE_BEAM"
echo " Optimizer beam: $COMBO_BEAM"
echo " Split: $SPLIT"
echo " Num samples: $NUM_SAMPLES (0 means full split)"
echo " Sample mode: $SAMPLE_MODE"
echo " Sample seed: $SAMPLE_SEED"
echo " Compute dtype: $COMPUTE_DTYPE"
echo " No resume: $NO_RESUME"
echo " MMR tri weights: $MMR_W_ROUGE/$MMR_W_MINICHECK/$MMR_W_REDUNDANCY"
echo " ILP/LNS soft per_edge weights: $SOFT_W_ROUGE/$SOFT_W_MINICHECK/$SOFT_W_REDUNDANCY"
echo " DPP tri weights: $DPP_W_ROUGE/$DPP_W_MINICHECK/$DPP_W_REDUNDANCY"
echo " Tri-metric weights are used as raw values; no sum-normalization."
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
echo " BART timed queue completed"
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
