#!/usr/bin/env bash
set -euo pipefail

ROOT=/path/to/NLP_generatesummary
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

SPLIT="${SPLIT:-validation}"
NUM_SAMPLES="${NUM_SAMPLES:-50}"
SAMPLE_MODE="${SAMPLE_MODE:-shuffle}"
SAMPLE_SEED="${SAMPLE_SEED:-42}"
BEAM_SIZE="${BEAM_SIZE:-10}"
COMPUTE_DTYPE="${COMPUTE_DTYPE:-bf16}"
OBJECTIVE="${OBJECTIVE:-minicheck_redundancy}"
THRESHOLDS="${THRESHOLDS:-0.60 0.55 0.50 0.45}"
RUN_ROOT="${RUN_ROOT:-$ROOT/bart/results/ilp_threshold_sweep_${OBJECTIVE}_${SPLIT}_n${NUM_SAMPLES}}"
SUMMARY_CSV="${SUMMARY_CSV:-$ROOT/bart/results/ilp_threshold_sweep_${OBJECTIVE}_${SPLIT}_n${NUM_SAMPLES}.csv}"

echo "=== ILP Threshold Sweep ==="
echo "SPLIT=$SPLIT"
echo "NUM_SAMPLES=$NUM_SAMPLES"
echo "SAMPLE_MODE=$SAMPLE_MODE"
echo "SAMPLE_SEED=$SAMPLE_SEED"
echo "BEAM_SIZE=$BEAM_SIZE"
echo "COMPUTE_DTYPE=$COMPUTE_DTYPE"
echo "OBJECTIVE=$OBJECTIVE"
echo "THRESHOLDS=$THRESHOLDS"
echo "RUN_ROOT=$RUN_ROOT"
echo "SUMMARY_CSV=$SUMMARY_CSV"

mkdir -p "$RUN_ROOT"

if [[ ! -f "$SUMMARY_CSV" ]]; then
  printf 'threshold,ROUGE-1,ROUGE-2,ROUGE-L,ROUGE-Lsum,BERTScore_F1,FactCC,MiniCheck,ResultFile\n' > "$SUMMARY_CSV"
fi

for threshold in $THRESHOLDS; do
  tag="${threshold/./p}"
  out_dir="$RUN_ROOT/thr_${tag}"
  result_file="$out_dir/beam${BEAM_SIZE}_ilp_${OBJECTIVE}_hfrouge"
  if [[ "$SPLIT" != "test" ]]; then
    result_file="${result_file}_${SPLIT}"
  fi
  if [[ "$SAMPLE_MODE" != "head" ]]; then
    result_file="${result_file}_${SAMPLE_MODE}_seed${SAMPLE_SEED}"
  fi
  result_file="${result_file}_results.txt"

  if [[ -f "$result_file" ]] && grep -q "SummaryAvgConsistent:" "$result_file"; then
    echo "[skip] threshold=$threshold -> $result_file"
  else
    echo "[run] threshold=$threshold"
    "$PYTHON" "$ROOT/bart/run.py" \
      --method ilp \
      --objective "$OBJECTIVE" \
      --split "$SPLIT" \
      --num-samples "$NUM_SAMPLES" \
      --sample-mode "$SAMPLE_MODE" \
      --sample-seed "$SAMPLE_SEED" \
      --beam-size "$BEAM_SIZE" \
      --compute-dtype "$COMPUTE_DTYPE" \
      --redundancy-threshold-override "$threshold" \
      --output-dir "$out_dir"
  fi

  "$PYTHON" - <<PY
import csv
import re
from pathlib import Path

summary_path = Path(r"$SUMMARY_CSV")
result_path = Path(r"$result_file")
threshold = "$threshold"

patterns = {
    "ROUGE-1": re.compile(r"^\\s*rouge1\\s+F1=([-\\d.]+)%$"),
    "ROUGE-2": re.compile(r"^\\s*rouge2\\s+F1=([-\\d.]+)%$"),
    "ROUGE-L": re.compile(r"^\\s*rougeL\\s+F1=([-\\d.]+)%$"),
    "ROUGE-Lsum": re.compile(r"^\\s*rougeLsum\\s+F1=([-\\d.]+)%$"),
    "BERTScore_F1": re.compile(r"^\\s*Precision=[-\\d.]+%\\s+Recall=[-\\d.]+%\\s+F1=([-\\d.]+)%$"),
    "FactCC": re.compile(r"^\\s*SentenceAvgCorrect:\\s*([-\\d.]+)%$"),
    "MiniCheck": re.compile(r"^\\s*SummaryAvgConsistent:\\s*([-\\d.]+)%$"),
}

row = {
    "threshold": threshold,
    "ROUGE-1": "",
    "ROUGE-2": "",
    "ROUGE-L": "",
    "ROUGE-Lsum": "",
    "BERTScore_F1": "",
    "FactCC": "",
    "MiniCheck": "",
    "ResultFile": str(result_path),
}

for line in result_path.read_text(encoding="utf-8", errors="replace").splitlines():
    for key, pattern in patterns.items():
        match = pattern.search(line)
        if match:
            row[key] = match.group(1)

rows = []
if summary_path.exists():
    with summary_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
rows = [existing for existing in rows if existing.get("threshold") != threshold]
rows.append(row)
rows.sort(key=lambda item: float(item["threshold"]))

with summary_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=[
        "threshold","ROUGE-1","ROUGE-2","ROUGE-L","ROUGE-Lsum","BERTScore_F1",
        "FactCC","MiniCheck","ResultFile"
    ])
    writer.writeheader()
    writer.writerows(rows)
PY
done

echo "Sweep complete."
echo "Summary CSV: $SUMMARY_CSV"
