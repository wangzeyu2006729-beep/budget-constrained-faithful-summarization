from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pick one shared tri-metric weight row from the cross-method apply CSV."
    )
    parser.add_argument("--input-csv", type=Path, required=True, help="Apply-shortlist CSV to read.")
    parser.add_argument("--output-csv", type=Path, required=True, help="Where to write the selected shared row(s).")
    parser.add_argument("--fact-key", default="MiniCheck", help="Fact metric column to maximize.")
    parser.add_argument("--anchor-method", default=None, help="Optional anchor method whose ROUGE floor must hold.")
    parser.add_argument(
        "--anchor-rouge1-floor",
        type=float,
        default=None,
        help="Optional ROUGE-1 floor that the anchor method must satisfy.",
    )
    parser.add_argument(
        "--avg-rouge1-floor",
        type=float,
        default=None,
        help="Optional average ROUGE-1 floor across all applied methods.",
    )
    parser.add_argument("--top-k", type=int, default=1, help="Write the top-k rows.")
    return parser.parse_args()


def _parse_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value in ("", None):
        return default
    return float(value)


def _weight_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("w_rouge", ""),
        row.get("w_minicheck", ""),
        row.get("w_redundancy", ""),
    )


def main() -> None:
    args = parse_args()

    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise SystemExit(f"No rows found in {args.input_csv}")

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[_weight_key(row)].append(row)

    aggregates: list[dict[str, object]] = []
    selection_mode = "unconstrained"
    for (w_rouge, w_minicheck, w_redundancy), bucket in grouped.items():
        fact_scores = [_parse_float(row, args.fact_key, default=-1.0) for row in bucket]
        rouge_1_scores = [_parse_float(row, "ROUGE-1") for row in bucket]
        rouge_2_scores = [_parse_float(row, "ROUGE-2") for row in bucket]
        rouge_l_scores = [_parse_float(row, "ROUGE-L") for row in bucket]
        runtimes = [_parse_float(row, "Runtime_sec") for row in bucket]
        method_names = [row.get("method", "") for row in bucket]

        anchor_row = None
        if args.anchor_method:
            for row in bucket:
                if row.get("method") == args.anchor_method:
                    anchor_row = row
                    break

        aggregates.append(
            {
                "w_rouge": w_rouge,
                "w_minicheck": w_minicheck,
                "w_redundancy": w_redundancy,
                "avg_fact_score": sum(fact_scores) / len(fact_scores),
                "avg_rouge1": sum(rouge_1_scores) / len(rouge_1_scores),
                "avg_rouge2": sum(rouge_2_scores) / len(rouge_2_scores),
                "avg_rouge_l": sum(rouge_l_scores) / len(rouge_l_scores),
                "min_fact_score": min(fact_scores),
                "min_rouge1": min(rouge_1_scores),
                "avg_runtime_sec": sum(runtimes) / len(runtimes),
                "method_count": len(bucket),
                "methods": " ".join(sorted(method_names)),
                "anchor_rouge1": None if anchor_row is None else _parse_float(anchor_row, "ROUGE-1"),
                "anchor_fact_score": None if anchor_row is None else _parse_float(anchor_row, args.fact_key, default=-1.0),
            }
        )

    eligible = list(aggregates)
    if args.anchor_rouge1_floor is not None and args.anchor_method:
        constrained = [
            row
            for row in eligible
            if row["anchor_rouge1"] is not None and row["anchor_rouge1"] >= args.anchor_rouge1_floor
        ]
        if constrained:
            selection_mode = "anchor_rouge1_floor"
            eligible = constrained

    if args.avg_rouge1_floor is not None:
        constrained = [row for row in eligible if row["avg_rouge1"] >= args.avg_rouge1_floor]
        if constrained:
            selection_mode = "avg_rouge1_floor"
            eligible = constrained

    ranked = sorted(
        eligible,
        key=lambda row: (
            row["avg_fact_score"],
            row["avg_rouge1"],
            row["avg_rouge2"],
            row["min_fact_score"],
            -row["avg_runtime_sec"],
        ),
        reverse=True,
    )
    selected = ranked[: max(1, args.top_k)]

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "rank",
            "method",
            "w_rouge",
            "w_minicheck",
            "w_redundancy",
            "fact_key",
            "selection_mode",
            "avg_fact_score",
            "avg_rouge1",
            "avg_rouge2",
            "avg_rouge_l",
            "min_fact_score",
            "min_rouge1",
            "method_count",
            "methods",
            "anchor_method",
            "anchor_rouge1_floor",
            "anchor_rouge1",
            "anchor_fact_score",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, row in enumerate(selected, start=1):
            writer.writerow(
                {
                    "rank": str(rank),
                    "method": "",
                    "w_rouge": row["w_rouge"],
                    "w_minicheck": row["w_minicheck"],
                    "w_redundancy": row["w_redundancy"],
                    "fact_key": args.fact_key,
                    "selection_mode": selection_mode,
                    "avg_fact_score": f"{row['avg_fact_score']:.4f}",
                    "avg_rouge1": f"{row['avg_rouge1']:.4f}",
                    "avg_rouge2": f"{row['avg_rouge2']:.4f}",
                    "avg_rouge_l": f"{row['avg_rouge_l']:.4f}",
                    "min_fact_score": f"{row['min_fact_score']:.4f}",
                    "min_rouge1": f"{row['min_rouge1']:.4f}",
                    "method_count": str(row["method_count"]),
                    "methods": row["methods"],
                    "anchor_method": args.anchor_method or "",
                    "anchor_rouge1_floor": "" if args.anchor_rouge1_floor is None else f"{args.anchor_rouge1_floor:.4f}",
                    "anchor_rouge1": "" if row["anchor_rouge1"] is None else f"{row['anchor_rouge1']:.4f}",
                    "anchor_fact_score": "" if row["anchor_fact_score"] is None else f"{row['anchor_fact_score']:.4f}",
                }
            )

    for rank, row in enumerate(selected, start=1):
        print(
            f"[rank {rank}] shared weights=({row['w_rouge']}, {row['w_minicheck']}, {row['w_redundancy']}) "
            f"| avg {args.fact_key}={row['avg_fact_score']:.4f} "
            f"| avg ROUGE-1={row['avg_rouge1']:.4f} "
            f"| min {args.fact_key}={row['min_fact_score']:.4f}"
        )
    print(f"Wrote: {args.output_csv}")


if __name__ == "__main__":
    main()
