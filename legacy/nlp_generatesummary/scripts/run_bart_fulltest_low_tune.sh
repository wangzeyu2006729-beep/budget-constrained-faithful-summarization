#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

export HF_HOME="${HF_HOME:-/path/to/NLM_data/hf_cache}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-$HF_HOME}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-$HF_HOME}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export HF_DATASETS_OFFLINE="${HF_DATASETS_OFFLINE:-1}"

SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-0}"
SAMPLE_MODE="${SAMPLE_MODE:-head}"
BEAM_SIZE="${BEAM_SIZE:-10}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
INCLUDE_MBR="${INCLUDE_MBR:-0}"
INCLUDE_BASELINE_RAW="${INCLUDE_BASELINE_RAW:-0}"
EXPLICIT_TRI_METHODS="${EXPLICIT_TRI_METHODS:-mmr}"
EXPLICIT_W_ROUGE="${EXPLICIT_W_ROUGE:-0.0}"
EXPLICIT_W_MINICHECK="${EXPLICIT_W_MINICHECK:-0.5}"
EXPLICIT_W_REDUNDANCY="${EXPLICIT_W_REDUNDANCY:-0.5}"
SOFT_TRI_METHODS="${SOFT_TRI_METHODS:-ilp lns}"
SOFT_W_ROUGE="${SOFT_W_ROUGE:-0.10}"
SOFT_W_MINICHECK="${SOFT_W_MINICHECK:-0.20}"
SOFT_W_REDUNDANCY="${SOFT_W_REDUNDANCY:-0.70}"
SOFT_PENALTY_SCALE="${SOFT_PENALTY_SCALE:-per_edge}"
NONWEIGHT_METHODS="${NONWEIGHT_METHODS:-dpp submodular}"
NONWEIGHT_OBJECTIVE="${NONWEIGHT_OBJECTIVE:-minicheck_redundancy}"
INCLUDE_PARETO="${INCLUDE_PARETO:-1}"
FORCE_RERUN="${FORCE_RERUN:-0}"

read -r -a EXPLICIT_TRI_METHOD_ARGS <<< "$EXPLICIT_TRI_METHODS"
read -r -a SOFT_TRI_METHOD_ARGS <<< "$SOFT_TRI_METHODS"
read -r -a NONWEIGHT_METHOD_ARGS <<< "$NONWEIGHT_METHODS"

weight_tag() {
  printf '%0.2f' "$1" | sed 's/\./p/g'
}

weight_tag_compact() {
  printf '%0.2f' "$1" | sed 's/^0\.//; s/\.//g'
}

run_one() {
  local method="$1"
  local objective="$2"
  local result_dir="$3"
  local result_file="$4"
  local result_path="$ROOT/bart/results/$result_dir/$result_file"

  if [[ "$FORCE_RERUN" != "1" ]] && [[ -f "$result_path" ]] && grep -q "SummaryAvgConsistent:" "$result_path"; then
    echo "[skip] $method ${objective:-summary} -> $result_path"
    return
  fi

  local -a cmd=(
    "$PYTHON" "$ROOT/bart/run.py"
    --method "$method"
    --split "$SPLIT"
    --num-samples "$NUM_SAMPLES"
    --sample-mode "$SAMPLE_MODE"
    --beam-size "$BEAM_SIZE"
    --compute-dtype "$COMPUTE_DTYPE"
  )
  if [[ -n "$objective" ]]; then
    cmd+=(--objective "$objective")
  fi

  echo "[run] $method ${objective:-summary}"
  "${cmd[@]}"
}

run_one_fixed_tri() {
  local method="$1"
  local wr_tag
  local wm_tag
  local wd_tag
  wr_tag="$(weight_tag "$EXPLICIT_W_ROUGE")"
  wm_tag="$(weight_tag "$EXPLICIT_W_MINICHECK")"
  wd_tag="$(weight_tag "$EXPLICIT_W_REDUNDANCY")"
  local result_dir="${method}_tri_metric_wr${wr_tag}_wm${wm_tag}_wd${wd_tag}"
  if [[ "$method" == "mmr" && "$EXPLICIT_W_ROUGE" == "0.0" && "$EXPLICIT_W_MINICHECK" == "0.5" && "$EXPLICIT_W_REDUNDANCY" == "0.5" ]]; then
    result_dir="mmr_tri_metric"
  fi
  local result_file="beam${BEAM_SIZE}_${method}_tri_metric_hfrouge_results.txt"
  local result_path="$ROOT/bart/results/$result_dir/$result_file"

  if [[ "$FORCE_RERUN" != "1" ]] && [[ -f "$result_path" ]] && grep -q "SummaryAvgConsistent:" "$result_path"; then
    echo "[skip] $method tri_metric_fixed -> $result_path"
    return
  fi

  local -a cmd=(
    "$PYTHON" "$ROOT/bart/run.py"
    --method "$method"
    --output-dir "$ROOT/bart/results/$result_dir"
    --split "$SPLIT"
    --num-samples "$NUM_SAMPLES"
    --sample-mode "$SAMPLE_MODE"
    --beam-size "$BEAM_SIZE"
    --compute-dtype "$COMPUTE_DTYPE"
    --tri-metric
    --w-rouge "$EXPLICIT_W_ROUGE"
    --w-minicheck "$EXPLICIT_W_MINICHECK"
    --w-redundancy "$EXPLICIT_W_REDUNDANCY"
  )

  echo "[run] $method tri_metric_fixed (${EXPLICIT_W_ROUGE}/${EXPLICIT_W_MINICHECK}/${EXPLICIT_W_REDUNDANCY})"
  "${cmd[@]}"
}

run_one_soft_tri() {
  local method="$1"
  local soft_name
  local penalty_arg
  case "$method" in
    ilp)
      soft_name="softilp"
      penalty_arg="--ilp-penalty-scale"
      ;;
    lns)
      soft_name="softlns"
      penalty_arg="--lns-penalty-scale"
      ;;
    *)
      echo "[error] soft tri-metric default only supports ilp/lns, got: $method" >&2
      return 2
      ;;
  esac

  local wr_tag
  local wm_tag
  local wd_tag
  wr_tag="$(weight_tag_compact "$SOFT_W_ROUGE")"
  wm_tag="$(weight_tag_compact "$SOFT_W_MINICHECK")"
  wd_tag="$(weight_tag_compact "$SOFT_W_REDUNDANCY")"
  local result_dir="${method}_tri_metric_${soft_name}_${SOFT_PENALTY_SCALE}_wr${wr_tag}_wm${wm_tag}_wd${wd_tag}"
  local result_file="beam${BEAM_SIZE}_${method}_tri_metric_hfrouge_results.txt"
  local result_path="$ROOT/bart/results/$result_dir/$result_file"

  if [[ "$FORCE_RERUN" != "1" ]] && [[ -f "$result_path" ]] && grep -q "SummaryAvgConsistent:" "$result_path"; then
    echo "[skip] $method ${soft_name}_${SOFT_PENALTY_SCALE} -> $result_path"
    return
  fi

  local -a cmd=(
    "$PYTHON" "$ROOT/bart/run.py"
    --method "$method"
    --output-dir "$ROOT/bart/results/$result_dir"
    --split "$SPLIT"
    --num-samples "$NUM_SAMPLES"
    --sample-mode "$SAMPLE_MODE"
    --beam-size "$BEAM_SIZE"
    --compute-dtype "$COMPUTE_DTYPE"
    --tri-metric
    --w-rouge "$SOFT_W_ROUGE"
    --w-minicheck "$SOFT_W_MINICHECK"
    --w-redundancy "$SOFT_W_REDUNDANCY"
    "$penalty_arg" "$SOFT_PENALTY_SCALE"
  )

  echo "[run] $method ${soft_name}_${SOFT_PENALTY_SCALE} (${SOFT_W_ROUGE}/${SOFT_W_MINICHECK}/${SOFT_W_REDUNDANCY})"
  "${cmd[@]}"
}

echo "=== Main Full-Test Batch ==="
echo "SPLIT=$SPLIT"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "SAMPLE_MODE=$SAMPLE_MODE"
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "INCLUDE_MBR=$INCLUDE_MBR"
echo "INCLUDE_BASELINE_RAW=$INCLUDE_BASELINE_RAW"
echo "EXPLICIT_TRI_METHODS=$EXPLICIT_TRI_METHODS"
echo "EXPLICIT_TRI_WEIGHTS=$EXPLICIT_W_ROUGE/$EXPLICIT_W_MINICHECK/$EXPLICIT_W_REDUNDANCY"
echo "SOFT_TRI_METHODS=$SOFT_TRI_METHODS"
echo "SOFT_TRI_WEIGHTS=$SOFT_W_ROUGE/$SOFT_W_MINICHECK/$SOFT_W_REDUNDANCY"
echo "SOFT_PENALTY_SCALE=$SOFT_PENALTY_SCALE"
echo "NONWEIGHT_METHODS=$NONWEIGHT_METHODS"
echo "NONWEIGHT_OBJECTIVE=$NONWEIGHT_OBJECTIVE"
echo "INCLUDE_PARETO=$INCLUDE_PARETO"
echo "FORCE_RERUN=$FORCE_RERUN"
echo "HF_HOME=$HF_HOME"
echo "HF_HUB_OFFLINE=$HF_HUB_OFFLINE"
echo "TRANSFORMERS_OFFLINE=$TRANSFORMERS_OFFLINE"
echo "HF_DATASETS_OFFLINE=$HF_DATASETS_OFFLINE"

if [[ "$INCLUDE_BASELINE_RAW" == "1" ]]; then
  run_one baseline_raw "" "baseline_raw_baseline_raw" "beam${BEAM_SIZE}_baseline_raw_hfrouge_results.txt"
fi

for method in "${EXPLICIT_TRI_METHOD_ARGS[@]}"; do
  run_one_fixed_tri "$method"
done

for method in "${SOFT_TRI_METHOD_ARGS[@]}"; do
  run_one_soft_tri "$method"
done

for method in "${NONWEIGHT_METHOD_ARGS[@]}"; do
  run_one "$method" "$NONWEIGHT_OBJECTIVE" "${method}_${NONWEIGHT_OBJECTIVE}" "beam${BEAM_SIZE}_${method}_${NONWEIGHT_OBJECTIVE}_hfrouge_results.txt"
done

if [[ "$INCLUDE_PARETO" == "1" ]]; then
  run_one pareto "" "pareto_summary_pareto" "beam${BEAM_SIZE}_pareto_hfrouge_results.txt"
fi

if [[ "$INCLUDE_MBR" == "1" ]]; then
  run_one mbr "" "mbr_summary_mbr" "beam${BEAM_SIZE}_mbr_hfrouge_results.txt"
fi

echo "Batch complete."
