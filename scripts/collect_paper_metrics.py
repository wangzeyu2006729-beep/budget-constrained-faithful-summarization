#!/usr/bin/env python3
"""Collect compact metrics from copied *_results.txt files."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = ROOT / "results" / "raw"
DEFAULT_OUTPUT_CSV = ROOT / "results" / "paper_metrics.csv"

HEADER_KEYS = [
    "Generator",
    "Method",
    "Objective variant",
    "Model",
    "Dataset",
    "Split",
    "Samples",
    "Sample mode",
    "Sample seed",
    "Beam size",
    "Candidate count",
    "Budget",
    "Runtime dtype",
    "ROUGE implementation",
    "ROUGE sentence split",
    "Ordering",
    "Tri-metric weights",
    "Stage1 reuse source",
]

METRIC_PATTERNS = {
    "rouge1": re.compile(r"^\s*rouge1\s+F1=([-\d.]+)%"),
    "rouge2": re.compile(r"^\s*rouge2\s+F1=([-\d.]+)%"),
    "rougeL": re.compile(r"^\s*rougeL\s+F1=([-\d.]+)%"),
    "rougeLsum": re.compile(r"^\s*rougeLsum\s+F1=([-\d.]+)%"),
    "bertscore_f1": re.compile(r"^\s*Precision=[-\d.]+%\s+Recall=[-\d.]+%\s+F1=([-\d.]+)%"),
    "factcc": re.compile(r"^\s*SentenceAvgCorrect:\s*([-\d.]+)%"),
    "minicheck": re.compile(r"^\s*SummaryAvgConsistent:\s*([-\d.]+)%"),
    "alignscore": re.compile(r"^\s*SummaryAvg:\s*([-\d.]+)%"),
    "factkb": re.compile(r"^\s*FactualProb:\s*([-\d.]+)%"),
}

FIELDNAMES = [
    "dataset",
    "generator",
    "method",
    "model",
    "samples",
    "sample_mode",
    "sample_seed",
    "candidate_count",
    "beam_size",
    "budget",
    "tri_metric_weights",
    "rouge1",
    "rouge2",
    "rougeL",
    "rougeLsum",
    "bertscore_f1",
    "factcc",
    "minicheck",
    "alignscore",
    "factkb",
    "factgraph_status",
    "ordering",
    "stage1_reuse_source",
    "source_result",
]


def parse_result(path: Path, root: Path) -> dict[str, str]:
    row: dict[str, str] = {field: "" for field in FIELDNAMES}
    row["source_result"] = str(path.relative_to(root))

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        for key in HEADER_KEYS:
            prefix = f"{key}: "
            if line.startswith(prefix):
                normalized = key.lower().replace(" ", "_").replace("-", "_")
                if normalized == "objective_variant":
                    normalized = "objective"
                if normalized in row:
                    row[normalized] = line[len(prefix):].strip()

        for metric_name, pattern in METRIC_PATTERNS.items():
            match = pattern.search(line)
            if match and not row[metric_name]:
                row[metric_name] = match.group(1)

        if line.startswith("FactGraph:"):
            row["factgraph_status"] = line.split(":", 1)[1].strip()

    return row


def sort_key(row: dict[str, str]) -> tuple[str, str, str, str]:
    return (
        row.get("dataset", ""),
        row.get("generator", ""),
        row.get("method", ""),
        row.get("source_result", ""),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    args = parser.parse_args()

    results_root = args.results_root.resolve()
    rows = [
        parse_result(path, results_root)
        for path in sorted(results_root.rglob("*_results.txt"))
    ]
    rows.sort(key=sort_key)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[collect] wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
