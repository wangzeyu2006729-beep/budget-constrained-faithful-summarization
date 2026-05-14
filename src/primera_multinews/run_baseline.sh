#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
DATASET="${DATASET:-multi_news}"
SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-0}"
SAMPLE_MODE="${SAMPLE_MODE:-shuffle}"
SAMPLE_SEED="${SAMPLE_SEED:-42}"
BEAM_SIZE="${BEAM_SIZE:-5}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
GENERATION_BATCH_SIZE="${GENERATION_BATCH_SIZE:-2}"
UTILITY_BATCH_SIZE="${UTILITY_BATCH_SIZE:-}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-}"
OUTPUT_TAG="${OUTPUT_TAG:-}"
RESUME_LATEST_PROGRESS="${RESUME_LATEST_PROGRESS:-0}"
DRY_RUN="${DRY_RUN:-0}"

build_output_dir() {
  local output_root="$ROOT/outputs/$DATASET/primera_multinews/baseline"
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
if [[ -n "$UTILITY_BATCH_SIZE" ]]; then
  EXTRA_ARGS+=(--utility-batch-size "$UTILITY_BATCH_SIZE")
fi
if [[ -n "$EVAL_BATCH_SIZE" ]]; then
  EXTRA_ARGS+=(--eval-batch-size "$EVAL_BATCH_SIZE")
fi
EXTRA_ARGS+=(--output-dir "$OUTPUT_DIR")

"$PYTHON" "$SCRIPT_DIR/run.py" \
  --method baseline \
  --generator primera_multinews \
  --dataset "$DATASET" \
  --split "$SPLIT" \
  --num-samples "$NUM_SAMPLES" \
  --sample-mode "$SAMPLE_MODE" \
  --sample-seed "$SAMPLE_SEED" \
  --beam-size "$BEAM_SIZE" \
  --generation-batch-size "$GENERATION_BATCH_SIZE" \
  --compute-dtype "$COMPUTE_DTYPE" \
  "${EXTRA_ARGS[@]}"
