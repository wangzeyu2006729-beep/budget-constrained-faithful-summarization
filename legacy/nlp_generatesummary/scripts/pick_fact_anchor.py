from __future__ import annotations

import argparse
import csv
import json
import shlex
from pathlib import Path


OPTIMIZABLE_METHODS = {"ilp", "mmr", "dpp", "submodular", "lns", "mbr", "pareto"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pick the fact-strongest method from an existing summary CSV."
    )
    parser.add_argument("--input-csv", type=Path, required=True, help="Existing summary metrics CSV.")
    parser.add_argument("--fact-key", default="MiniCheck", help="Fact metric column to maximize.")
    parser.add_argument("--split", default=None, help="Optional split filter (for example: test).")
    parser.add_argument(
        "--prefer-optimizable",
        action="store_true",
        help="Also choose the best search anchor among optimizable methods.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "env"],
        default="text",
        help="Output format.",
    )
    parser.add_argument("--output-json", type=Path, default=None, help="Optional JSON report path.")
    return parser.parse_args()


def _parse_float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value in ("", None):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _weight_metadata(method: str, objective: str) -> tuple[bool, str, str]:
    if method in {"baseline_raw", "baseline3"}:
        return False, "none", "baseline generation only; no optimization weights"

    if method == "mbr" and objective == "Summary-level MBR":
        return True, "fixed_scalar", "consensus=0.3, minicheck=0.7"

    if method == "pareto" and objective == "Summary-level PARETO":
        return False, "priority_only", "MiniCheck > Coverage > -Redundancy"

    if objective == "MiniCheck only":
        return False, "objective_variant", "utility=minicheck, redundancy=off"

    if objective == "MiniCheck + Redundancy":
        return False, "objective_variant", "utility=minicheck, redundancy=on"

    if objective == "ROUGE only":
        return False, "objective_variant", "utility=rouge, redundancy=off"

    if objective == "ROUGE + Redundancy":
        return False, "objective_variant", "utility=rouge, redundancy=on"

    return False, "unknown", "unrecognized objective variant"


def _rank_key(row: dict[str, str], fact_key: str) -> tuple[float, float, float, float]:
    fact = _parse_float(row, fact_key)
    rouge_1 = _parse_float(row, "ROUGE-1")
    rouge_2 = _parse_float(row, "ROUGE-2")
    rouge_l = _parse_float(row, "ROUGE-L")
    return (
        -1.0 if fact is None else fact,
        -1.0 if rouge_1 is None else rouge_1,
        -1.0 if rouge_2 is None else rouge_2,
        -1.0 if rouge_l is None else rouge_l,
    )


def _build_report(row: dict[str, str], fact_key: str) -> dict[str, object]:
    method = row.get("Method", "")
    objective = row.get("Objective", "")
    has_explicit_weights, weight_mode, weight_note = _weight_metadata(method, objective)
    return {
        "method": method,
        "objective": objective,
        "budget": row.get("Budget", ""),
        "split": row.get("Split", ""),
        "fact_key": fact_key,
        "fact_score": _parse_float(row, fact_key),
        "rouge_1": _parse_float(row, "ROUGE-1"),
        "rouge_2": _parse_float(row, "ROUGE-2"),
        "rouge_l": _parse_float(row, "ROUGE-L"),
        "optimizable": method in OPTIMIZABLE_METHODS,
        "has_explicit_weights": has_explicit_weights,
        "weight_mode": weight_mode,
        "weight_note": weight_note,
    }


def _emit_env(payload: dict[str, object]) -> str:
    lines: list[str] = []
    for key, value in payload.items():
        env_key = key.upper()
        if isinstance(value, bool):
            env_value = "1" if value else "0"
        elif value is None:
            env_value = ""
        else:
            env_value = str(value)
        lines.append(f"{env_key}={shlex.quote(env_value)}")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if args.split:
        rows = [row for row in rows if row.get("Split") == args.split]

    scored_rows = [row for row in rows if _parse_float(row, args.fact_key) is not None]
    if not scored_rows:
        raise SystemExit(f"No usable {args.fact_key!r} rows found in {args.input_csv}")

    overall_best = max(scored_rows, key=lambda row: _rank_key(row, args.fact_key))

    if args.prefer_optimizable:
        optimizable_rows = [
            row for row in scored_rows if row.get("Method", "") in OPTIMIZABLE_METHODS
        ]
        if not optimizable_rows:
            raise SystemExit(f"No optimizable rows found in {args.input_csv}")
        anchor_best = max(optimizable_rows, key=lambda row: _rank_key(row, args.fact_key))
    else:
        anchor_best = overall_best

    report = {
        "overall_fact_method": overall_best.get("Method", ""),
        "overall_fact_objective": overall_best.get("Objective", ""),
        "overall_fact_budget": overall_best.get("Budget", ""),
        "overall_fact_split": overall_best.get("Split", ""),
        "overall_fact_score": _parse_float(overall_best, args.fact_key),
        "overall_rouge1": _parse_float(overall_best, "ROUGE-1"),
        "overall_rouge2": _parse_float(overall_best, "ROUGE-2"),
        "overall_rouge_l": _parse_float(overall_best, "ROUGE-L"),
        "overall_optimizable": overall_best.get("Method", "") in OPTIMIZABLE_METHODS,
    }
    report.update(
        {
            f"overall_{key}": value
            for key, value in _build_report(overall_best, args.fact_key).items()
            if key not in {"method", "objective", "budget", "split", "fact_key", "fact_score", "rouge_1", "rouge_2", "rouge_l", "optimizable"}
        }
    )

    anchor_report = _build_report(anchor_best, args.fact_key)
    report.update(
        {
            "search_anchor_method": anchor_report["method"],
            "search_anchor_objective": anchor_report["objective"],
            "search_anchor_budget": anchor_report["budget"],
            "search_anchor_split": anchor_report["split"],
            "search_anchor_fact_key": anchor_report["fact_key"],
            "search_anchor_fact_score": anchor_report["fact_score"],
            "search_anchor_rouge1": anchor_report["rouge_1"],
            "search_anchor_rouge2": anchor_report["rouge_2"],
            "search_anchor_rouge_l": anchor_report["rouge_l"],
            "search_anchor_optimizable": anchor_report["optimizable"],
            "search_anchor_has_explicit_weights": anchor_report["has_explicit_weights"],
            "search_anchor_weight_mode": anchor_report["weight_mode"],
            "search_anchor_weight_note": anchor_report["weight_note"],
        }
    )

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return

    if args.format == "env":
        print(_emit_env(report))
        return

    print(
        "overall best "
        f"{args.fact_key}={report['overall_fact_score']:.2f} "
        f"method={report['overall_fact_method']} "
        f"objective={report['overall_fact_objective']!r}"
    )
    print(
        "search anchor "
        f"method={report['search_anchor_method']} "
        f"objective={report['search_anchor_objective']!r} "
        f"{args.fact_key}={report['search_anchor_fact_score']:.2f} "
        f"ROUGE-1={report['search_anchor_rouge1']:.2f} "
        f"weight_mode={report['search_anchor_weight_mode']} "
        f"explicit_weights={'yes' if report['search_anchor_has_explicit_weights'] else 'no'}"
    )
    print(f"weight note: {report['search_anchor_weight_note']}")


if __name__ == "__main__":
    main()
