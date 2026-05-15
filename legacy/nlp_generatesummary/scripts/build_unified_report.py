from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from unified_eval_common import (
    build_markdown_table,
    choose_primary_fact_metric,
    comparable_500,
    discover_methods,
    ensure_output_dir,
    format_score,
    metric_value,
    sort_methods_for_report,
    summarize_paper_reference,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a factuality-first unified comparison report.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where unified comparison artifacts will be written.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=500,
        help="Comparable sample threshold used in the report (default: 500).",
    )
    return parser.parse_args()


def choose_project_best(methods: list[dict[str, object]], primary_fact_key: str) -> dict[str, object] | None:
    candidates = [entry for entry in methods if entry.get("project_family") == "bart_beam_combopt"]
    candidates = [entry for entry in candidates if comparable_500(entry, fact_key=primary_fact_key)]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            metric_value(item, primary_fact_key) or -1e9,
            metric_value(item, "rouge1") or -1e9,
        ),
    )


def choose_high_rouge_low_fact(methods: list[dict[str, object]], primary_fact_key: str) -> dict[str, object] | None:
    candidates = [entry for entry in methods if comparable_500(entry, fact_key=primary_fact_key)]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            (metric_value(item, "rouge1") or -1e9) - (metric_value(item, primary_fact_key) or -1e9),
            metric_value(item, "rouge1") or -1e9,
        ),
    )


def choose_high_fact_mid_rouge(methods: list[dict[str, object]], primary_fact_key: str) -> dict[str, object] | None:
    candidates = [entry for entry in methods if comparable_500(entry, fact_key=primary_fact_key)]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            (metric_value(item, primary_fact_key) or -1e9) - (metric_value(item, "rouge1") or -1e9),
            metric_value(item, primary_fact_key) or -1e9,
        ),
    )


def paper_sanity_summary(methods: list[dict[str, object]], sample_limit: int) -> list[str]:
    comparable = []
    for entry in methods:
        reference = entry.get("paper_reference") or {}
        metrics = reference.get("metrics") or {}
        if not metrics or int(entry.get("current_samples") or 0) < sample_limit:
            continue
        if metric_value(entry, "rouge1") is None or metrics.get("rouge1") is None:
            continue
        comparable.append((abs((metric_value(entry, "rouge1") or 0.0) - float(metrics["rouge1"])), entry))

    if not comparable:
        return [
            "No method currently has both a 500-sample local result and a directly comparable paper reference in this workspace."
        ]

    comparable.sort(key=lambda item: item[0])
    return [f"{entry['method_id']}: Delta R1={delta:.2f} versus paper reference." for delta, entry in comparable[:5]]


def build_csv_rows(methods: list[dict[str, object]], primary_fact_key: str) -> list[dict[str, object]]:
    rows = []
    for entry in methods:
        notes = []
        if int(entry.get("current_samples") or 0) and int(entry.get("current_samples") or 0) < 500:
            notes.append(f"Only {entry['current_samples']} samples currently available.")
        if entry.get("missing_prerequisites"):
            notes.append("Missing prerequisites: " + "; ".join(entry["missing_prerequisites"]))
        if entry.get("notes"):
            notes.append(str(entry["notes"]))
        reference = entry.get("paper_reference") or {}
        if reference.get("comparability"):
            notes.append("Paper comparability: " + str(reference["comparability"]))

        rows.append(
            {
                "method": entry["method_id"],
                "paper/source": entry.get("paper_source", ""),
                "paper reference score": summarize_paper_reference(entry),
                "status": entry.get("status", ""),
                "current_samples": entry.get("current_samples", ""),
                "ROUGE-1": format_score(metric_value(entry, "rouge1")),
                "ROUGE-2": format_score(metric_value(entry, "rouge2")),
                "ROUGE-L": format_score(metric_value(entry, "rougeL")),
                "MiniCheck": format_score(metric_value(entry, "minicheck")),
                "FactCC": format_score(metric_value(entry, "factcc")),
                "runtime": "",
                "notes": " ".join(notes).strip(),
                "current_result_file": entry.get("current_result_file", "")
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    output_dir = ensure_output_dir(args.output_dir)
    primary_fact = choose_primary_fact_metric()
    methods = sort_methods_for_report(discover_methods(), primary_fact["metric_key"])
    csv_rows = build_csv_rows(methods, primary_fact["metric_key"])

    csv_path = output_dir / "unified_comparison.csv"
    md_path = output_dir / "unified_comparison.md"
    analysis_path = output_dir / "unified_analysis.json"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    project_best = choose_project_best(methods, primary_fact["metric_key"])
    high_rouge_low_fact = choose_high_rouge_low_fact(methods, primary_fact["metric_key"])
    high_fact_mid_rouge = choose_high_fact_mid_rouge(methods, primary_fact["metric_key"])
    paper_sanity = paper_sanity_summary(methods, args.sample_limit)

    analysis = {
        "primary_fact_metric": primary_fact,
        "project_best_method": project_best["method_id"] if project_best else None,
        "project_best_fact_score": metric_value(project_best, primary_fact["metric_key"]) if project_best else None,
        "project_best_rouge1": metric_value(project_best, "rouge1") if project_best else None,
        "high_rouge_low_fact_method": high_rouge_low_fact["method_id"] if high_rouge_low_fact else None,
        "high_fact_mid_rouge_method": high_fact_mid_rouge["method_id"] if high_fact_mid_rouge else None,
        "paper_sanity_summary": paper_sanity,
    }
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    md_rows = []
    for row in csv_rows:
        md_rows.append(
            {
                "method": row["method"],
                "paper/source": row["paper/source"],
                "paper reference score": row["paper reference score"],
                "samples": row["current_samples"],
                "ROUGE-1": row["ROUGE-1"],
                "ROUGE-2": row["ROUGE-2"],
                "ROUGE-L": row["ROUGE-L"],
                primary_fact["name"]: row[primary_fact["name"]],
                "status": row["status"],
                "notes": row["notes"],
            }
        )

    md_text = "\n".join(
        [
            "# Unified Comparison",
            "",
            f"Primary FACT metric: **{primary_fact['name']}**",
            "",
            "Reasoning:",
            *[f"- {reason}" for reason in primary_fact["reasons"]],
            "",
            build_markdown_table(
                md_rows,
                [
                    ("method", "method"),
                    ("paper/source", "paper/source"),
                    ("paper reference score", "paper reference score"),
                    ("samples", "samples"),
                    ("ROUGE-1", "ROUGE-1"),
                    ("ROUGE-2", "ROUGE-2"),
                    ("ROUGE-L", "ROUGE-L"),
                    (primary_fact["name"], primary_fact["name"]),
                    ("status", "status"),
                    ("notes", "notes"),
                ],
            ),
            "",
            "## Factuality-first analysis",
            "",
            (
                f"- Best method inside the project's BART + beam + combinatorial-optimization family: "
                f"`{project_best['method_id']}` with {primary_fact['name']}="
                f"{metric_value(project_best, primary_fact['metric_key']):.2f} and ROUGE-1="
                f"{metric_value(project_best, 'rouge1'):.2f}."
                if project_best
                else "- No project-family method currently has a comparable 500-sample FACT score."
            ),
            (
                f"- ROUGE-high but FACT-lower pattern: `{high_rouge_low_fact['method_id']}`."
                if high_rouge_low_fact
                else "- No comparable 500-sample method was available for the ROUGE-vs-FACT contrast."
            ),
            (
                f"- FACT-high with more modest ROUGE pattern: `{high_fact_mid_rouge['method_id']}`."
                if high_fact_mid_rouge
                else "- No comparable 500-sample method was available for the FACT-vs-ROUGE contrast."
            ),
            "",
            "## Paper sanity anchors",
            "",
            *[f"- {line}" for line in paper_sanity],
            "",
        ]
    )
    md_path.write_text(md_text, encoding="utf-8")

    print(csv_path)
    print(md_path)
    print(analysis_path)


if __name__ == "__main__":
    main()
