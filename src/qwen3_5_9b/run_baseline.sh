#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
DATASET="${DATASET:-cnn_dailymail}"
SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-0}"
SAMPLE_MODE="${SAMPLE_MODE:-shuffle}"
SAMPLE_SEED="${SAMPLE_SEED:-42}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
MAX_INPUT_TOKENS="${MAX_INPUT_TOKENS:-}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-}"
GENERATION_BATCH_SIZE="${GENERATION_BATCH_SIZE:-}"
UTILITY_BATCH_SIZE="${UTILITY_BATCH_SIZE:-}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-}"
OUTPUT_TAG="${OUTPUT_TAG:-}"
RESUME_LATEST_PROGRESS="${RESUME_LATEST_PROGRESS:-0}"
DRY_RUN="${DRY_RUN:-0}"

build_output_dir() {
  local output_root="$ROOT/outputs/$DATASET/qwen3_5_9b/baseline"
  local progress_dir=""
  if [[ -n "$OUTPUT_TAG" ]]; then
    echo "$output_root/full_${DATASET}_baseline_${OUTPUT_TAG}"
    return
  fi
  if [[ "$RESUME_LATEST_PROGRESS" == "1" && -d "$output_root" ]]; then
    progress_dir="$(
      find "$output_root" -mindepth 2 -maxdepth 2 -type f -name '*_progress.json' -printf '%T@ %h\n' 2>/dev/null \
        | sort -nr \
        | head -n 1 \
        | cut -d' ' -f2-
    )"
  fi
  if [[ -n "$progress_dir" ]]; then
    echo "$progress_dir"
    return
  fi
  echo "$output_root/full_${DATASET}_baseline_$(date +%Y%m%d_%H%M%S)"
}

OUTPUT_DIR="$(build_output_dir)"

if [[ "$DRY_RUN" == "1" ]]; then
  mkdir -p "$OUTPUT_DIR"
  printf 'dry_run=1\nscript=%s\noutput_dir=%s\n' "$0" "$OUTPUT_DIR" > "$OUTPUT_DIR/dry_run_marker.txt"
  echo "[run_baseline] dry-run validated; output dir prepared: $OUTPUT_DIR"
  exit 0
fi

EXTRA_ARGS=()
if [[ -n "$MAX_INPUT_TOKENS" ]]; then
  EXTRA_ARGS+=(--max-input-tokens "$MAX_INPUT_TOKENS")
fi
if [[ -n "$MAX_NEW_TOKENS" ]]; then
  EXTRA_ARGS+=(--max-new-tokens "$MAX_NEW_TOKENS")
fi
if [[ -n "$GENERATION_BATCH_SIZE" ]]; then
  EXTRA_ARGS+=(--generation-batch-size "$GENERATION_BATCH_SIZE")
fi
if [[ -n "$UTILITY_BATCH_SIZE" ]]; then
  EXTRA_ARGS+=(--utility-batch-size "$UTILITY_BATCH_SIZE")
fi
if [[ -n "$EVAL_BATCH_SIZE" ]]; then
  EXTRA_ARGS+=(--eval-batch-size "$EVAL_BATCH_SIZE")
fi
EXTRA_ARGS+=(--output-dir "$OUTPUT_DIR")

"$PYTHON" "$SCRIPT_DIR/run.py" \
  --method baseline \
  --generator qwen3.5_9B \
  --dataset "$DATASET" \
  --split "$SPLIT" \
  --num-samples "$NUM_SAMPLES" \
  --sample-mode "$SAMPLE_MODE" \
  --sample-seed "$SAMPLE_SEED" \
  --compute-dtype "$COMPUTE_DTYPE" \
  "${EXTRA_ARGS[@]}"
