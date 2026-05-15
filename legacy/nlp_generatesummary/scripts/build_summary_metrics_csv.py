from __future__ import annotations

import argparse
import csv
import io
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ROOT / "bart" / "results"
DEFAULT_BEAM_SIZE = 5
DEFAULT_OUTPUT_CSV = RESULTS_ROOT / f"summary_metrics_beam{DEFAULT_BEAM_SIZE}_hfrouge.csv"

METHOD_ORDER = {
    "baseline3": 0,
    "baseline_raw": 1,
    "dpp": 2,
    "ilp": 3,
    "lns": 4,
    "mbr": 5,
    "mmr": 6,
    "pareto": 7,
    "submodular": 8,
}

OBJECTIVE_ORDER = {
    "Baseline3 (Top-1 Beam -> First 4 Sentences)": 0,
    "Baseline3 (Top-1 Beam -> First 3 Sentences)": 0,
    "Raw Baseline (Top-1 Beam, Full Output)": 0,
    "MiniCheck only": 1,
    "MiniCheck + Redundancy": 2,
    "ROUGE only": 3,
    "ROUGE + Redundancy": 4,
    "Summary-level MBR": 5,
    "Summary-level PARETO": 6,
}

SPLIT_ORDER = {"test": 0, "validation": 1, "train": 2}

FIELDNAMES = [
    "Method",
    "Objective",
    "Budget",
    "Split",
    "ROUGE-1",
    "ROUGE-2",
    "ROUGE-L",
    "ROUGE-Lsum",
    "BERTScore_F1",
    "FactCC",
    "MiniCheck",
]

PROJECT_DIRS = [
    "baseline3_baseline3",
    "baseline_raw_baseline_raw",
    "dpp_minicheck_only",
    "dpp_minicheck_redundancy",
    "dpp_rouge_only",
    "dpp_rouge_redundancy",
    "ilp_minicheck_only",
    "ilp_minicheck_redundancy",
    "ilp_rouge_only",
    "ilp_rouge_redundancy",
    "lns_minicheck_only",
    "lns_minicheck_redundancy",
    "lns_rouge_only",
    "lns_rouge_redundancy",
    "mbr_summary_mbr",
    "mmr_minicheck_only",
    "mmr_minicheck_redundancy",
    "mmr_rouge_only",
    "mmr_rouge_redundancy",
    "pareto_summary_pareto",
    "submodular_minicheck_only",
    "submodular_minicheck_redundancy",
    "submodular_rouge_only",
    "submodular_rouge_redundancy",
]

KNOWN_NAMED_SPLITS = {"train", "validation"}

METHOD_RE = re.compile(r"^Method:\s*(.+)$")
OBJECTIVE_RE = re.compile(r"^Objective variant:\s*(.+)$")
BUDGET_RE = re.compile(r"^Budget:\s*(.+)$")
SPLIT_RE = re.compile(r"^Split:\s*(train|validation|test)$")
ROUGE_F1_RE = re.compile(r"^\s*(rouge1|rouge2|rougeL|rougeLsum)\s+F1=([-\d.]+)%$")
ROUGE_PRF_RE = re.compile(
    r"^\s*(rouge1|rouge2|rougeL|rougeLsum)\s+Precision=([-\d.]+)%\s+Recall=([-\d.]+)%\s+F1=([-\d.]+)%$"
)
BERTSCORE_RE = re.compile(r"^\s*Precision=([-\d.]+)%\s+Recall=([-\d.]+)%\s+F1=([-\d.]+)%$")
BARTSCORE_SRC_RE = re.compile(r"^\s*src->hyp:\s*([-\d.]+)$")
ENTAILMENT_RE = re.compile(r"^\s*Entailment:\s*([-\d.]+)%$")
FACTCC_RE = re.compile(r"^\s*SentenceAvgCorrect:\s*([-\d.]+)%$")
MINICHECK_RE = re.compile(r"^\s*SummaryAvgConsistent:\s*([-\d.]+)%$")
ALIGNSCORE_RE = re.compile(r"^\s*SummaryAvg:\s*([-\d.]+)%$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild the project combinatorial-optimization summary CSV.")
    parser.add_argument(
        "--results-root",
        type=Path,
        default=RESULTS_ROOT,
        help="Directory containing per-experiment result folders.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="CSV file to write. Defaults to summary_metrics_beam{beam}_{rouge}.csv under --results-root.",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=DEFAULT_BEAM_SIZE,
        help=f"Beam size encoded in result filenames (default: {DEFAULT_BEAM_SIZE}).",
    )
    parser.add_argument(
        "--rouge-impl",
        choices=["hf", "local"],
        default="hf",
        help="ROUGE implementation encoded in result filenames (default: hf).",
    )
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Fail if the rebuilt rows do not match the existing output CSV.",
    )
    return parser.parse_args()


def result_file_matches(path: Path, beam_size: int, split: str, rouge_impl: str) -> bool:
    stem_parts = path.stem.split("_")
    if not stem_parts or stem_parts[0] != f"beam{beam_size}" or stem_parts[-1] != "results":
        return False

    has_hf_rouge = "hfrouge" in stem_parts
    if rouge_impl == "hf" and not has_hf_rouge:
        return False
    if rouge_impl == "local" and has_hf_rouge:
        return False

    file_split = "test"
    for candidate in KNOWN_NAMED_SPLITS:
        if candidate in stem_parts:
            file_split = candidate
            break
    return file_split == split


def find_result_file(experiment_dir: Path, beam_size: int, split: str, rouge_impl: str) -> Path:
    matches = [
        path
        for path in experiment_dir.glob("beam*_results.txt")
        if result_file_matches(path, beam_size=beam_size, split=split, rouge_impl=rouge_impl)
    ]
    matches = sorted(matches, key=lambda item: item.name)
    if not matches:
        raise FileNotFoundError(
            f"Missing result file under {experiment_dir} for beam={beam_size}, split={split}, rouge={rouge_impl}"
        )
    if len(matches) > 1:
        joined = ", ".join(path.name for path in matches)
        raise RuntimeError(
            f"Ambiguous result files under {experiment_dir} for beam={beam_size}, split={split}, rouge={rouge_impl}: "
            f"{joined}"
        )
    return matches[0]


def _format_percent(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def _format_bartscore(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"


def parse_result_file(path: Path) -> dict[str, str]:
    method = None
    objective = None
    budget = None
    split = None
    metrics: dict[str, float] = {}
    in_bertscore = False

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = METHOD_RE.search(line)
        if match:
            method = match.group(1).strip()
            continue

        match = OBJECTIVE_RE.search(line)
        if match:
            objective = match.group(1).strip()
            continue

        match = BUDGET_RE.search(line)
        if match:
            budget = match.group(1).strip()
            continue

        match = SPLIT_RE.search(line)
        if match:
            split = match.group(1).strip()
            continue

        match = ROUGE_PRF_RE.search(line)
        if match:
            metrics[match.group(1)] = float(match.group(4))
            continue

        match = ROUGE_F1_RE.search(line)
        if match:
            metrics[match.group(1)] = float(match.group(2))
            continue

        if line.startswith("BERTScore"):
            in_bertscore = True
            continue

        if in_bertscore:
            match = BERTSCORE_RE.search(line)
            if match:
                metrics["bertscore_f1"] = float(match.group(3))
                in_bertscore = False
            continue

        for regex, key in (
            (BARTSCORE_SRC_RE, "bartscore_src"),
            (ENTAILMENT_RE, "nli_entailment"),
            (FACTCC_RE, "factcc"),
            (MINICHECK_RE, "minicheck"),
            (ALIGNSCORE_RE, "alignscore"),
        ):
            match = regex.search(line)
            if match:
                metrics[key] = float(match.group(1))
                break

    if not method or not objective or not budget or not split:
        raise ValueError(f"Failed to parse required metadata from {path}")

    return {
        "Method": method,
        "Objective": objective,
        "Budget": budget,
        "Split": split,
        "ROUGE-1": _format_percent(metrics.get("rouge1")),
        "ROUGE-2": _format_percent(metrics.get("rouge2")),
        "ROUGE-L": _format_percent(metrics.get("rougeL")),
        "ROUGE-Lsum": _format_percent(metrics.get("rougeLsum")),
        "BERTScore_F1": _format_percent(metrics.get("bertscore_f1")),
        "FactCC": _format_percent(metrics.get("factcc")),
        "MiniCheck": _format_percent(metrics.get("minicheck")),
    }


def _sort_key(row: dict[str, str]) -> tuple[int, int, int, str, str]:
    return (
        METHOD_ORDER.get(row["Method"], 999),
        OBJECTIVE_ORDER.get(row["Objective"], 999),
        SPLIT_ORDER.get(row["Split"], 999),
        row["Method"],
        row["Objective"],
    )


def build_summary_rows(results_root: Path, beam_size: int = DEFAULT_BEAM_SIZE, rouge_impl: str = "hf") -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for directory_name in PROJECT_DIRS:
        experiment_dir = results_root / directory_name
        if not experiment_dir.exists():
            continue
        try:
            result_file = find_result_file(
                experiment_dir,
                beam_size=beam_size,
                split="test",
                rouge_impl=rouge_impl,
            )
        except FileNotFoundError:
            continue
        rows.append(parse_result_file(result_file))

    return sorted(rows, key=_sort_key)


def default_output_csv(results_root: Path, beam_size: int, rouge_impl: str) -> Path:
    rouge_tag = "hfrouge" if rouge_impl == "hf" else "localrouge"
    return results_root / f"summary_metrics_beam{beam_size}_{rouge_tag}.csv"


def load_existing_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def render_csv(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def compare_rows(expected: list[dict[str, str]], actual: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if len(expected) != len(actual):
        errors.append(f"row count mismatch: expected {len(expected)}, got {len(actual)}")
        return errors

    for index, (left, right) in enumerate(zip(expected, actual), start=1):
        if left == right:
            continue
        for field in FIELDNAMES:
            if left.get(field) != right.get(field):
                errors.append(
                    f"row {index} field {field!r}: expected {left.get(field)!r}, got {right.get(field)!r}"
                )
                break
    return errors


def write_if_changed(path: Path, rows: list[dict[str, str]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing_rows = load_existing_rows(path)
        if existing_rows == rows:
            return "unchanged"
    path.write_text(render_csv(rows), encoding="utf-8", newline="")
    return "written"


def main() -> None:
    args = parse_args()
    if args.output_csv is None:
        args.output_csv = default_output_csv(args.results_root, args.beam_size, args.rouge_impl)
    rows = build_summary_rows(args.results_root, beam_size=args.beam_size, rouge_impl=args.rouge_impl)

    if args.check_existing and args.output_csv.exists():
        errors = compare_rows(rows, load_existing_rows(args.output_csv))
        if errors:
            raise SystemExit("Existing CSV does not match rebuilt rows:\n" + "\n".join(errors[:20]))

    status = write_if_changed(args.output_csv, rows)
    print(f"{args.output_csv} ({status})")


if __name__ == "__main__":
    main()
