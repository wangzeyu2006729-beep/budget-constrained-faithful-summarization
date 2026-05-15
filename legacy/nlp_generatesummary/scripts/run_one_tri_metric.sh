#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

usage() {
  cat <<'EOF'
Usage:
  run_one_tri_metric.sh --name SESSION --method METHOD --w-rouge X --w-minicheck Y --w-redundancy Z

Optional:
  --split SPLIT                default: validation
  --num-samples N             default: 50
  --sample-mode MODE          default: shuffle
  --sample-seed SEED          default: 42
  --beam-size N               default: 10
  --compute-dtype DTYPE       default: bf16
  --output-dir DIR            default: auto-generated under bart/results

Example:
  bash scripts/run_one_tri_metric.sh \
    --name mmr_w0p0_m0p5_d0p5 \
    --method mmr \
    --w-rouge 0.0 \
    --w-minicheck 0.5 \
    --w-redundancy 0.5
EOF
}

NAME=""
METHOD=""
W_ROUGE=""
W_MINICHECK=""
W_REDUNDANCY=""
SPLIT="validation"
NUM_SAMPLES="50"
SAMPLE_MODE="shuffle"
SAMPLE_SEED="42"
BEAM_SIZE="10"
COMPUTE_DTYPE="bf16"
OUTPUT_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="${2:?}"; shift 2 ;;
    --method) METHOD="${2:?}"; shift 2 ;;
    --w-rouge) W_ROUGE="${2:?}"; shift 2 ;;
    --w-minicheck) W_MINICHECK="${2:?}"; shift 2 ;;
    --w-redundancy) W_REDUNDANCY="${2:?}"; shift 2 ;;
    --split) SPLIT="${2:?}"; shift 2 ;;
    --num-samples) NUM_SAMPLES="${2:?}"; shift 2 ;;
    --sample-mode) SAMPLE_MODE="${2:?}"; shift 2 ;;
    --sample-seed) SAMPLE_SEED="${2:?}"; shift 2 ;;
    --beam-size) BEAM_SIZE="${2:?}"; shift 2 ;;
    --compute-dtype) COMPUTE_DTYPE="${2:?}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$NAME" || -z "$METHOD" || -z "$W_ROUGE" || -z "$W_MINICHECK" || -z "$W_REDUNDANCY" ]]; then
  usage >&2
  exit 1
fi

tag() {
  printf "%.2f" "$1" | tr '.' 'p'
}

WR_TAG="$(tag "$W_ROUGE")"
WM_TAG="$(tag "$W_MINICHECK")"
WD_TAG="$(tag "$W_REDUNDANCY")"

if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$ROOT/bart/results/${METHOD}_tri_metric_wr${WR_TAG}_wm${WM_TAG}_wd${WD_TAG}_${SPLIT}_n${NUM_SAMPLES}_beam${BEAM_SIZE}"
fi

echo "SESSION=$NAME"
echo "METHOD=$METHOD"
echo "WEIGHTS=($W_ROUGE, $W_MINICHECK, $W_REDUNDANCY)"
echo "SPLIT=$SPLIT"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "SAMPLE_MODE=$SAMPLE_MODE"
echo "SAMPLE_SEED=$SAMPLE_SEED"
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "OUTPUT_DIR=$OUTPUT_DIR"

"$ROOT/scripts/run_persistent.sh" --name "$NAME" -- \
  "$PYTHON" "$ROOT/bart/run.py" \
  --method "$METHOD" \
  --output-dir "$OUTPUT_DIR" \
  --split "$SPLIT" \
  --num-samples "$NUM_SAMPLES" \
  --sample-mode "$SAMPLE_MODE" \
  --sample-seed "$SAMPLE_SEED" \
  --beam-size "$BEAM_SIZE" \
  --compute-dtype "$COMPUTE_DTYPE" \
  --tri-metric \
  --w-rouge "$W_ROUGE" \
  --w-minicheck "$W_MINICHECK" \
  --w-redundancy "$W_REDUNDANCY"
