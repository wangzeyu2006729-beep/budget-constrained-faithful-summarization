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
BEAM_SIZE="${BEAM_SIZE:-8}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
METHODS="${METHODS:-ilp dpp mmr}"
REUSE_STAGE1_FROM="${REUSE_STAGE1_FROM:-}"
LAST_STAGE1_TRACE=""
MAX_INPUT_TOKENS="${MAX_INPUT_TOKENS:-}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-}"
OUTPUT_TAG="${OUTPUT_TAG:-}"
RESUME_LATEST_PROGRESS="${RESUME_LATEST_PROGRESS:-0}"
DRY_RUN="${DRY_RUN:-0}"
CO_BUDGET_SENTENCES_OVERRIDE="${CO_BUDGET_SENTENCES:-${BUDGET_SENTENCES:-}}"
CO_UTILITY_BATCH_SIZE_OVERRIDE="${CO_UTILITY_BATCH_SIZE:-${UTILITY_BATCH_SIZE:-32}}"
CO_EVAL_BATCH_SIZE_OVERRIDE="${CO_EVAL_BATCH_SIZE:-${EVAL_BATCH_SIZE:-64}}"
CO_CHECKPOINT_INTERVAL_OVERRIDE="${CO_CHECKPOINT_INTERVAL:-${CHECKPOINT_INTERVAL:-}}"
CO_NO_RESUME="${CO_NO_RESUME:-${NO_RESUME:-0}}"

if [[ -z "$CO_BUDGET_SENTENCES_OVERRIDE" && "$DATASET" == "multi_news" ]]; then
  CO_BUDGET_SENTENCES_OVERRIDE=8
fi

build_output_dir() {
  local method="$1"
  local method_root="$ROOT/outputs/$DATASET/qwen3_5_9b/${method}"
  local progress_dir=""
  if [[ -n "$OUTPUT_TAG" ]]; then
    echo "$method_root/full_${DATASET}_co_tri_metric_${OUTPUT_TAG}"
    return
  fi
  if [[ "$RESUME_LATEST_PROGRESS" == "1" && -d "$method_root" ]]; then
    progress_dir="$(
      find "$method_root" -mindepth 2 -maxdepth 2 -type f -name '*_progress.json' -printf '%T@ %h\n' 2>/dev/null \
        | sort -nr \
        | head -n 1 \
        | cut -d' ' -f2-
    )"
  fi
  if [[ -n "$progress_dir" ]]; then
    echo "$progress_dir"
    return
  fi
  echo "$method_root/full_${DATASET}_co_tri_metric_$(date +%Y%m%d_%H%M%S)"
}

build_result_file() {
  local output_dir="$1"
  local method="$2"
  local parts=("beam${BEAM_SIZE}" "$method" "tri_metric" "hfrouge")
  if [[ "$SPLIT" != "test" ]]; then
    parts+=("$SPLIT")
  fi
  if [[ "$SAMPLE_MODE" != "head" ]]; then
    parts+=("$SAMPLE_MODE" "seed${SAMPLE_SEED}")
  fi
  local stem
  stem="$(IFS=_; echo "${parts[*]}")"
  echo "$output_dir/${stem}_results.txt"
}

find_stage1_trace() {
  local output_dir="$1"
  find "$output_dir" -maxdepth 1 -name '*_stage_outputs.jsonl' | sort | tail -n 1
}

for method in $METHODS; do
  case "$method" in
    dpp)
      W_ROUGE="${DPP_W_ROUGE:-0.01}"
      W_MINICHECK="${DPP_W_MINICHECK:-0.495}"
      W_REDUNDANCY="${DPP_W_REDUNDANCY:-0.495}"
      ;;
    mmr)
      W_ROUGE="${MMR_W_ROUGE:-0.01}"
      W_MINICHECK="${MMR_W_MINICHECK:-0.495}"
      W_REDUNDANCY="${MMR_W_REDUNDANCY:-0.495}"
      ;;
    ilp)
      W_ROUGE="${ILP_W_ROUGE:-0.01}"
      W_MINICHECK="${ILP_W_MINICHECK:-0.495}"
      W_REDUNDANCY="${ILP_W_REDUNDANCY:-0.495}"
      ;;
    *)
      echo "Unsupported method: $method" >&2
      exit 2
      ;;
  esac

  # beam=8, batch=12 is the default LLM CO generation target for resumed runs.
  CO_GEN_BATCH="${CO_GENERATION_BATCH_SIZE:-12}"
  OUTPUT_DIR="$(build_output_dir "$method")"
  RESULT_FILE="$(build_result_file "$OUTPUT_DIR" "$method")"
  EXTRA_ARGS=()
  if [[ -n "$MAX_INPUT_TOKENS" ]]; then
    EXTRA_ARGS+=(--max-input-tokens "$MAX_INPUT_TOKENS")
  fi
  if [[ -n "$MAX_NEW_TOKENS" ]]; then
    EXTRA_ARGS+=(--max-new-tokens "$MAX_NEW_TOKENS")
  fi
  if [[ -n "$CO_UTILITY_BATCH_SIZE_OVERRIDE" ]]; then
    EXTRA_ARGS+=(--utility-batch-size "$CO_UTILITY_BATCH_SIZE_OVERRIDE")
  fi
  if [[ -n "$CO_EVAL_BATCH_SIZE_OVERRIDE" ]]; then
    EXTRA_ARGS+=(--eval-batch-size "$CO_EVAL_BATCH_SIZE_OVERRIDE")
  fi
  if [[ -n "$CO_BUDGET_SENTENCES_OVERRIDE" ]]; then
    EXTRA_ARGS+=(--budget-sentences "$CO_BUDGET_SENTENCES_OVERRIDE")
  fi
  if [[ -n "$CO_CHECKPOINT_INTERVAL_OVERRIDE" ]]; then
    EXTRA_ARGS+=(--checkpoint-interval "$CO_CHECKPOINT_INTERVAL_OVERRIDE")
  fi
  if [[ "$CO_NO_RESUME" == "1" ]]; then
    EXTRA_ARGS+=(--no-resume)
  fi
  if [[ "$method" != "ilp" ]]; then
    REUSE_SOURCE="${REUSE_STAGE1_FROM:-$LAST_STAGE1_TRACE}"
    if [[ -n "$REUSE_SOURCE" ]]; then
      EXTRA_ARGS+=(--reuse-stage1-from "$REUSE_SOURCE")
      echo "[run_methods] $method will reuse stage1 from: $REUSE_SOURCE"
    fi
  fi

  if [[ -f "$RESULT_FILE" ]]; then
    echo "[run_methods] $method already complete; skipping: $RESULT_FILE"
    if [[ "$method" == "ilp" ]]; then
      LAST_STAGE1_TRACE="$(find_stage1_trace "$OUTPUT_DIR")"
      if [[ -z "$LAST_STAGE1_TRACE" ]]; then
        echo "[run_methods] failed to locate ILP stage_outputs.jsonl in $OUTPUT_DIR" >&2
        exit 3
      fi
      echo "[run_methods] captured ILP stage1 trace: $LAST_STAGE1_TRACE"
    fi
    continue
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    mkdir -p "$OUTPUT_DIR"
    if [[ "$method" == "ilp" ]]; then
      LAST_STAGE1_TRACE="$OUTPUT_DIR/dry_run_${method}_stage_outputs.jsonl"
      printf '{"dry_run": true, "method": "%s"}\n' "$method" > "$LAST_STAGE1_TRACE"
      echo "[run_methods] dry-run validated $method; prepared stage1 trace: $LAST_STAGE1_TRACE"
    else
      if [[ -z "${REUSE_SOURCE:-}" || ! -f "$REUSE_SOURCE" ]]; then
        echo "[run_methods] dry-run missing reuse source for $method: ${REUSE_SOURCE:-<empty>}" >&2
        exit 3
      fi
      echo "[run_methods] dry-run validated $method with reuse source: $REUSE_SOURCE"
    fi
    continue
  fi

  "$PYTHON" "$SCRIPT_DIR/run.py" \
    --method "$method" \
    --generator qwen3.5_9B \
    --dataset "$DATASET" \
    --split "$SPLIT" \
    --num-samples "$NUM_SAMPLES" \
    --sample-mode "$SAMPLE_MODE" \
    --sample-seed "$SAMPLE_SEED" \
    --beam-size "$BEAM_SIZE" \
    --generation-batch-size "$CO_GEN_BATCH" \
    --compute-dtype "$COMPUTE_DTYPE" \
    --tri-metric \
    --w-rouge "$W_ROUGE" --w-minicheck "$W_MINICHECK" --w-redundancy "$W_REDUNDANCY" \
    --output-dir "$OUTPUT_DIR" \
    "${EXTRA_ARGS[@]}"

  if [[ "$method" == "ilp" ]]; then
    LAST_STAGE1_TRACE="$(find_stage1_trace "$OUTPUT_DIR")"
    if [[ -z "$LAST_STAGE1_TRACE" ]]; then
      echo "[run_methods] failed to locate ILP stage_outputs.jsonl in $OUTPUT_DIR" >&2
      exit 3
    fi
    echo "[run_methods] captured ILP stage1 trace: $LAST_STAGE1_TRACE"
  fi
done
