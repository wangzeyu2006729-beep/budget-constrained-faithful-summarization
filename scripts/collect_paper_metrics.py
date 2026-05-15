#!/usr/bin/env python3
"""Collect compact metrics for rows reported in the current paper table."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = ROOT / "results" / "raw"
DEFAULT_OUTPUT_CSV = ROOT / "results" / "paper_metrics.csv"

REPORTED_CURRENT_PAPER_ROWS = {
    ("cnn_dailymail", "bart", "baseline"),
    ("cnn_dailymail", "qwen3.5_9B", "baseline"),
    ("cnn_dailymail", "llama3_8b", "baseline"),
    ("cnn_dailymail", "gemma_4_e4b", "baseline"),
    ("cnn_dailymail", "bart", "mmr"),
    ("cnn_dailymail", "bart", "ilp"),
    ("cnn_dailymail", "bart", "dpp"),
    ("cnn_dailymail", "llama3_8b", "mmr"),
    ("cnn_dailymail", "llama3_8b", "ilp"),
    ("cnn_dailymail", "llama3_8b", "dpp"),
    ("multi_news", "primera_multinews", "baseline"),
    ("multi_news", "primera_multinews", "mmr"),
    ("multi_news", "primera_multinews", "ilp"),
    ("multi_news", "primera_multinews", "dpp"),
}

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

UNAVAILABLE_PATTERNS = {
    "bertscore_status": re.compile(r"^BERTScore:\s*unavailable\s*(.*)$"),
    "factcc_status": re.compile(r"^FactCC:\s*unavailable\s*(.*)$"),
    "minicheck_status": re.compile(r"^MiniCheck:\s*unavailable\s*(.*)$"),
    "alignscore_status": re.compile(r"^AlignScore:\s*unavailable\s*(.*)$"),
    "factkb_status": re.compile(r"^FactKB:\s*unavailable\s*(.*)$"),
    "factgraph_status": re.compile(r"^FactGraph:\s*unavailable\s*(.*)$"),
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
    "bertscore_status",
    "factcc",
    "factcc_status",
    "minicheck",
    "minicheck_status",
    "alignscore",
    "alignscore_status",
    "factkb",
    "factkb_status",
    "factgraph_status",
    "ordering",
    "stage1_reuse_source",
    "source_type",
    "budget_table_status",
    "source_result",
]


def parse_result(path: Path, root: Path) -> dict[str, str]:
    row: dict[str, str] = {field: "" for field in FIELDNAMES}
    row["source_type"] = "result_txt"
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

        for status_name, pattern in UNAVAILABLE_PATTERNS.items():
            match = pattern.search(line)
            if match and not row[status_name]:
                detail = match.group(1).strip()
                row[status_name] = f"unavailable {detail}".strip()

    return row


def normalize_dataset(dataset: str) -> str:
    return dataset.split(" ", 1)[0].strip()


def infer_generator(row: dict[str, str]) -> str:
    generator = row.get("generator", "").strip()
    if generator:
        return generator

    model = row.get("model", "")
    source = row.get("source_result", "")
    if "bart-large-cnn" in model or "/bart/" in source:
        return "bart"
    if "Qwen3.5-9B" in model:
        return "qwen3.5_9B"
    if "Llama-3.1-8B" in model:
        return "llama3_8b"
    if "gemma-4-E4B" in model:
        return "gemma_4_e4b"
    return generator


def normalize_method(method: str) -> str:
    if method == "baseline_raw":
        return "baseline"
    return method


def normalize_row(row: dict[str, str]) -> None:
    row["dataset"] = normalize_dataset(row.get("dataset", ""))
    row["generator"] = infer_generator(row)
    row["method"] = normalize_method(row.get("method", ""))
    if not row.get("candidate_count") and row.get("beam_size"):
        row["candidate_count"] = row["beam_size"]


def annotate_current_paper_table_status(row: dict[str, str]) -> None:
    key = (row.get("dataset", ""), row.get("generator", ""), row.get("method", ""))
    if key in REPORTED_CURRENT_PAPER_ROWS:
        row["budget_table_status"] = "reported local row in current paper table"
    else:
        row["budget_table_status"] = "not reported in current paper table"


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
    for row in rows:
        normalize_row(row)
        annotate_current_paper_table_status(row)
    rows = [
        row
        for row in rows
        if row.get("budget_table_status") == "reported local row in current paper table"
    ]
    rows.sort(key=sort_key)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[collect] wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
