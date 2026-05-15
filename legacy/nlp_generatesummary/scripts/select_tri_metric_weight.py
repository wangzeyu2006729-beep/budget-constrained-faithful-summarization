from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pick one tri-metric weight row from a completed grid-search CSV."
    )
    parser.add_argument("--input-csv", type=Path, required=True, help="Grid-search CSV to read.")
    parser.add_argument("--output-csv", type=Path, required=True, help="Where to write the selected weight row.")
    parser.add_argument("--method", default="mmr", help="Representative method to filter on.")
    parser.add_argument("--split", default="validation", help="Split to filter on.")
    parser.add_argument("--num-samples", type=int, default=20, help="NumSamples to filter on.")
    parser.add_argument(
        "--select-by",
        choices=["rouge_mean", "rouge_1", "rouge_l", "rouge_2", "minicheck"],
        default="rouge_mean",
        help="Primary score reported in the output metadata.",
    )
    parser.add_argument(
        "--min-rouge1",
        type=float,
        default=None,
        help="Optional ROUGE-1 floor. When set, rows must meet this threshold before fact priority is applied.",
    )
    parser.add_argument(
        "--fact-key",
        default="MiniCheck",
        help="Fact-style metric column to maximize once the ROUGE-1 constraint is satisfied.",
    )
    parser.add_argument(
        "--min-fact",
        type=float,
        default=None,
        help="Optional floor on the fact metric named by --fact-key.",
    )
    parser.add_argument(
        "--secondary-key",
        choices=["rouge_mean", "rouge_1", "rouge_2", "rouge_l", "minicheck", "none"],
        default="rouge_2",
        help="Tie-break metric used after fact maximization in constrained mode.",
    )
    parser.add_argument(
        "--tertiary-key",
        choices=["rouge_mean", "rouge_1", "rouge_2", "rouge_l", "minicheck", "none"],
        default="rouge_l",
        help="Second tie-break metric used after --secondary-key in constrained mode.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=1,
        help="Write the top-k selected rows instead of only the single best row.",
    )
    parser.add_argument(
        "--constraint-priority",
        choices=["fact_then_rouge", "rouge_then_fact"],
        default="fact_then_rouge",
        help="When constraint mode is active, rank feasible rows by fact first or ROUGE-1 first.",
    )
    return parser.parse_args()


def _parse_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value in (None, ""):
        return default
    return float(value)


def _selection_score(row: dict[str, str], select_by: str) -> float:
    if select_by == "rouge_1":
        return _parse_float(row, "ROUGE-1")
    if select_by == "rouge_l":
        return _parse_float(row, "ROUGE-L")
    if select_by == "rouge_2":
        return _parse_float(row, "ROUGE-2")
    if select_by == "minicheck":
        return _parse_float(row, "MiniCheck")
    rouge_1 = _parse_float(row, "ROUGE-1")
    rouge_2 = _parse_float(row, "ROUGE-2")
    rouge_l = _parse_float(row, "ROUGE-L")
    return (rouge_1 + rouge_2 + rouge_l) / 3.0


def _rank_metric(row: dict[str, str], metric_name: str) -> float:
    if metric_name == "none":
        return 0.0
    return _selection_score(row, metric_name)


def _row_rank_key(row: dict[str, str], select_by: str) -> tuple[float, float, float, float]:
    return (
        _selection_score(row, select_by),
        _parse_float(row, "MiniCheck", default=-1.0),
        _parse_float(row, "ROUGE-2"),
        -_parse_float(row, "Runtime_sec"),
    )


def _constrained_rank_key(
    row: dict[str, str],
    fact_key: str,
    secondary_key: str,
    tertiary_key: str,
    constraint_priority: str,
) -> tuple[float, float, float, float, float, float]:
    rouge_1 = _parse_float(row, "ROUGE-1")
    fact_score = _parse_float(row, fact_key, default=-1.0)
    rouge_2 = _parse_float(row, "ROUGE-2")
    secondary_score = _rank_metric(row, secondary_key)
    tertiary_score = _rank_metric(row, tertiary_key)
    runtime_score = -_parse_float(row, "Runtime_sec")
    if constraint_priority == "rouge_then_fact":
        return (
            rouge_1,
            fact_score,
            secondary_score,
            tertiary_score,
            rouge_2,
            runtime_score,
        )
    return (
        fact_score,
        secondary_score,
        tertiary_score,
        rouge_1,
        rouge_2,
        runtime_score,
    )


def _closest_threshold_rank_key(
    row: dict[str, str],
    rouge_target: float,
    fact_key: str,
    secondary_key: str,
    tertiary_key: str,
) -> tuple[float, float, float, float, float, float]:
    rouge_1 = _parse_float(row, "ROUGE-1")
    return (
        -abs(rouge_1 - rouge_target),
        _parse_float(row, fact_key, default=-1.0),
        _rank_metric(row, secondary_key),
        _rank_metric(row, tertiary_key),
        rouge_1,
        _parse_float(row, "ROUGE-2"),
        -_parse_float(row, "Runtime_sec"),
    )


def main() -> None:
    args = parse_args()

    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    filtered = [
        row
        for row in rows
        if row.get("method") == args.method
        and row.get("Split") == args.split
        and row.get("NumSamples") == str(args.num_samples)
    ]
    if not filtered:
        raise SystemExit(
            f"No rows found for method={args.method!r}, split={args.split!r}, num_samples={args.num_samples} "
            f"in {args.input_csv}"
        )

    selection_mode = "unconstrained"
    threshold_met_count = ""
    fact_floor_met_count = ""
    if args.min_rouge1 is not None:
        rouge_eligible = [row for row in filtered if _parse_float(row, "ROUGE-1") >= args.min_rouge1]
        threshold_met_count = str(len(rouge_eligible))
        if args.min_fact is not None:
            eligible = [row for row in rouge_eligible if _parse_float(row, args.fact_key, default=-1.0) >= args.min_fact]
            fact_floor_met_count = str(len(eligible))
        else:
            eligible = list(rouge_eligible)

        if eligible:
            selection_mode = "constraint_satisfied"
            ranked = sorted(
                eligible,
                key=lambda row: _constrained_rank_key(
                    row,
                    args.fact_key,
                    args.secondary_key,
                    args.tertiary_key,
                    args.constraint_priority,
                ),
                reverse=True,
            )
        elif rouge_eligible:
            selection_mode = "fallback_fact_floor" if args.min_fact is not None else "constraint_satisfied"
            ranked = sorted(
                rouge_eligible,
                key=lambda row: _constrained_rank_key(
                    row,
                    args.fact_key,
                    args.secondary_key,
                    args.tertiary_key,
                    args.constraint_priority,
                ),
                reverse=True,
            )
        else:
            selection_mode = "fallback_closest_rouge1"
            ranked = sorted(
                filtered,
                key=lambda row: _closest_threshold_rank_key(
                    row,
                    args.min_rouge1,
                    args.fact_key,
                    args.secondary_key,
                    args.tertiary_key,
                ),
                reverse=True,
            )
    else:
        ranked = sorted(filtered, key=lambda row: _row_rank_key(row, args.select_by), reverse=True)

    selected_rows = ranked[: max(1, args.top_k)]

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "rank",
            "method",
            "w_rouge",
            "w_minicheck",
            "w_redundancy",
            "selected_by",
            "selection_score",
            "selection_mode",
            "fact_key",
            "fact_score",
            "min_rouge1",
            "min_fact",
            "threshold_met_count",
            "fact_floor_met_count",
            "secondary_key",
            "tertiary_key",
            "constraint_priority",
            "selected_rouge1",
            "source_method",
            "source_split",
            "source_num_samples",
            "source_result_file",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, best in enumerate(selected_rows, start=1):
            best_score = _selection_score(best, args.select_by)
            best_fact_score = _parse_float(best, args.fact_key, default=-1.0)
            writer.writerow(
                {
                    "rank": str(rank),
                    # Blank method means "apply this row to every method" in run_tri_metric_grid.py.
                    "method": "",
                    "w_rouge": best["w_rouge"],
                    "w_minicheck": best["w_minicheck"],
                    "w_redundancy": best["w_redundancy"],
                    "selected_by": args.select_by,
                    "selection_score": f"{best_score:.4f}",
                    "selection_mode": selection_mode,
                    "fact_key": args.fact_key,
                    "fact_score": f"{best_fact_score:.4f}" if best_fact_score >= 0 else "",
                    "min_rouge1": "" if args.min_rouge1 is None else f"{args.min_rouge1:.2f}",
                    "min_fact": "" if args.min_fact is None else f"{args.min_fact:.2f}",
                    "threshold_met_count": threshold_met_count,
                    "fact_floor_met_count": fact_floor_met_count,
                    "secondary_key": args.secondary_key,
                    "tertiary_key": args.tertiary_key,
                    "constraint_priority": args.constraint_priority,
                    "selected_rouge1": f"{_parse_float(best, 'ROUGE-1'):.4f}",
                    "source_method": args.method,
                    "source_split": args.split,
                    "source_num_samples": str(args.num_samples),
                    "source_result_file": best.get("ResultFile", ""),
                }
            )

    for rank, best in enumerate(selected_rows, start=1):
        best_score = _selection_score(best, args.select_by)
        best_fact_score = _parse_float(best, args.fact_key, default=-1.0)
        summary = (
            f"[rank {rank}] {args.method} "
            f"weights=({best['w_rouge']}, {best['w_minicheck']}, {best['w_redundancy']})"
        )
        if args.min_rouge1 is not None or args.min_fact is not None:
            summary += (
                f" | mode={selection_mode}"
                f" | ROUGE-1={_parse_float(best, 'ROUGE-1'):.4f}"
                f" | {args.fact_key}={best_fact_score:.4f}"
            )
        summary += f" | {args.select_by}={best_score:.4f}"
        print(summary)
    print(f"Wrote: {args.output_csv}")


if __name__ == "__main__":
    main()
