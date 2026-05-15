#!/usr/bin/env bash
# SimCLS train scorer from scratch using BRIO-shared cnndm/diverse data
set -euo pipefail
GPU="${GPU:-0}"
SIMCLS=/path/to/NLM_data/third_party/SimCLS-main
BRIO=/path/to/NLM_data/third_party/BRIO-main
LOG_DIR=$HOME/logs
mkdir -p "$LOG_DIR"

export HF_HOME=/path/to/NLM_data/hf_cache
export TRANSFORMERS_CACHE=$HF_HOME

# Reuse BRIO venv (same transformers 4.40, same torch 2.11)
source "$BRIO/.venv-brio/bin/activate"

export SIMCLS_BATCH_SIZE="${SIMCLS_BATCH_SIZE:-8}"
export SIMCLS_ACCUMULATE_STEP="${SIMCLS_ACCUMULATE_STEP:-1}"
export SIMCLS_NUM_WORKERS="${SIMCLS_NUM_WORKERS:-16}"
export SIMCLS_EVAL_BATCH_SIZE="${SIMCLS_EVAL_BATCH_SIZE:-16}"
export SIMCLS_PIN_MEMORY="${SIMCLS_PIN_MEMORY:-1}"
export SIMCLS_PERSISTENT_WORKERS="${SIMCLS_PERSISTENT_WORKERS:-1}"
export SIMCLS_ALLOW_TF32="${SIMCLS_ALLOW_TF32:-1}"
export SIMCLS_MAX_TRAIN_SAMPLES="${SIMCLS_MAX_TRAIN_SAMPLES:--1}"
export SIMCLS_MAX_VAL_SAMPLES="${SIMCLS_MAX_VAL_SAMPLES:--1}"
export SIMCLS_MAX_UPDATE_STEPS="${SIMCLS_MAX_UPDATE_STEPS:--1}"

cd "$SIMCLS"
mkdir -p cache result

# Patch: default dataset xsum -> cnndm (idempotent)
python3 - <<PY
import re, pathlib
p = pathlib.Path("main.py")
s = p.read_text()
s2 = s.replace("args.dataset = getattr(args, \"dataset\", \"xsum\")",
               "args.dataset = getattr(args, \"dataset\", \"cnndm\")")
if s != s2:
    p.write_text(s2)
    print("patched dataset default -> cnndm")
else:
    print("already patched")
PY

echo "=== GPU ==="
nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv
echo "=== data check ==="
ls -la cnndm/diverse/ | head
echo "train samples: $(ls cnndm/diverse/train | wc -l)"
echo "val samples:   $(ls cnndm/diverse/val | wc -l)"
echo "test samples:  $(ls cnndm/diverse/test | wc -l)"
echo "=== runtime ==="
echo "SIMCLS_BATCH_SIZE=$SIMCLS_BATCH_SIZE"
echo "SIMCLS_ACCUMULATE_STEP=$SIMCLS_ACCUMULATE_STEP"
echo "SIMCLS_NUM_WORKERS=$SIMCLS_NUM_WORKERS"
echo "SIMCLS_EVAL_BATCH_SIZE=$SIMCLS_EVAL_BATCH_SIZE"
echo "SIMCLS_MAX_TRAIN_SAMPLES=$SIMCLS_MAX_TRAIN_SAMPLES"
echo "SIMCLS_MAX_VAL_SAMPLES=$SIMCLS_MAX_VAL_SAMPLES"
echo "SIMCLS_MAX_UPDATE_STEPS=$SIMCLS_MAX_UPDATE_STEPS"

TS=$(date +%m%d_%H%M)
LOG="$LOG_DIR/simcls_train_$TS.log"
echo "=== train (log: $LOG) ==="
CUDA_VISIBLE_DEVICES=$GPU python -u main.py --cuda --gpuid 0 -l 2>&1 | tee "$LOG"
