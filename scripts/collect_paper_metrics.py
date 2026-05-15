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


def parse_bart_archive_csv(path: Path, root: Path) -> list[dict[str, str]]:
    """Parse the archived BART selector summary CSV.

    The original full BART selector result text files were not present in the
    source tree. This CSV still supports the CNN/DM BART selector rows, but it
    lacks BERTScore and FactKB, so those fields are explicit missing statuses.
    """
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for archive_row in reader:
            method = archive_row.get("method", "").strip()
            beam_size = archive_row.get("beam_size", "").strip()
            if beam_size != "5":
                continue

            row: dict[str, str] = {field: "" for field in FIELDNAMES}
            row.update(
                {
                    "dataset": "cnn_dailymail",
                    "generator": "bart",
                    "method": method,
                    "model": "facebook/bart-large-cnn",
                    "samples": archive_row.get("samples", "").strip(),
                    "sample_mode": "shuffle",
                    "sample_seed": archive_row.get("sample_seed", "").strip(),
                    "candidate_count": beam_size,
                    "beam_size": beam_size,
                    "budget": archive_row.get("budget", "").strip(),
                    "rouge1": archive_row.get("rouge1_f1", "").strip(),
                    "rouge2": archive_row.get("rouge2_f1", "").strip(),
                    "rougeL": archive_row.get("rougeL_f1", "").strip(),
                    "rougeLsum": archive_row.get("rougeLsum_f1", "").strip(),
                    "bertscore_status": "missing from archived summary CSV",
                    "factcc": archive_row.get("factcc", "").strip(),
                    "minicheck": archive_row.get("minicheck", "").strip(),
                    "alignscore": archive_row.get("alignscore", "").strip(),
                    "factkb_status": "missing from archived summary CSV",
                    "factgraph_status": "not reported in archived summary CSV",
                    "ordering": "not recorded in archived summary CSV",
                    "source_type": "archived_summary_csv",
                    "source_result": (
                        f"{path.relative_to(root)}#"
                        f"{method}-beam{beam_size}"
                    ),
                }
            )

            weight_scheme = archive_row.get("weight_scheme", "").strip()
            has_effective_weights = bool(
                archive_row.get("effective_w_rouge", "").strip()
                or archive_row.get("effective_w_minicheck", "").strip()
                or archive_row.get("effective_w_redundancy", "").strip()
            )
            if has_effective_weights:
                row["tri_metric_weights"] = (
                    f"scheme={weight_scheme}; "
                    f"rouge={archive_row.get('effective_w_rouge', '').strip()}, "
                    f"minicheck={archive_row.get('effective_w_minicheck', '').strip()}, "
                    f"redundancy={archive_row.get('effective_w_redundancy', '').strip()}"
                )
            elif weight_scheme:
                row["tri_metric_weights"] = weight_scheme

            rows.append(row)

    return rows


def annotate_budget_table_status(row: dict[str, str]) -> None:
    dataset = row.get("dataset", "")
    generator = row.get("generator", "")
    method = row.get("method", "")
    source = row.get("source_result", "")

    if dataset == "multi_news" and generator == "bart":
        row["budget_table_status"] = "extra result; not a Budget paper table row"
    elif dataset == "cnn_dailymail" and generator == "bart":
        row["budget_table_status"] = "partial Budget table evidence from archive"
    elif (
        dataset == "cnn_dailymail"
        and generator == "llama3_8b"
        and method in {"ilp", "mmr"}
    ):
        if "balanced_wr020_wm060_wd020" in source:
            row["budget_table_status"] = "matches Budget table new-weight row"
        else:
            row["budget_table_status"] = "extra old-weight result"
    elif (
        dataset == "cnn_dailymail"
        and generator == "llama3_8b"
        and method == "dpp"
    ):
        if "requested_full_resume" in source:
            row["budget_table_status"] = "matches Budget table old-weight row"
        else:
            row["budget_table_status"] = "extra new-weight result"
    elif dataset == "multi_news" and generator in {"qwen3.5_9B", "gemma_4_e4b"}:
        row["budget_table_status"] = "available for blank Budget table baseline row"
    else:
        row["budget_table_status"] = "matches or supports Budget table"


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
    for path in sorted(results_root.rglob("*weights_annotated.csv")):
        rows.extend(parse_bart_archive_csv(path, results_root))
    for row in rows:
        annotate_budget_table_status(row)
    rows = [
        row
        for row in rows
        if row.get("budget_table_status") != "extra result; not a Budget paper table row"
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
