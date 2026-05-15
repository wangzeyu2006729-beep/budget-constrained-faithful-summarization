from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = ROOT / "bart" / "results"
DEFAULT_PLOTS_DIR = DEFAULT_RESULTS_ROOT / "plots"


EXPERIMENT_ORDER = [
    "baseline_raw_baseline_raw",
    "baseline3_baseline3",
    "ilp_rouge_only",
    "mmr_rouge_only",
    "dpp_rouge_only",
    "submodular_rouge_only",
    "lns_rouge_only",
    "ilp_rouge_redundancy",
    "mmr_rouge_redundancy",
    "dpp_rouge_redundancy",
    "submodular_rouge_redundancy",
    "lns_rouge_redundancy",
    "ilp_minicheck_only",
    "mmr_minicheck_only",
    "dpp_minicheck_only",
    "submodular_minicheck_only",
    "lns_minicheck_only",
    "ilp_minicheck_redundancy",
    "mmr_minicheck_redundancy",
    "dpp_minicheck_redundancy",
    "submodular_minicheck_redundancy",
    "lns_minicheck_redundancy",
    "mbr_summary_mbr",
    "pareto_summary_pareto",
]

GROUP_TITLES = {
    "baseline": "Baselines",
    "rouge_only": "ROUGE Only",
    "rouge_redundancy": "ROUGE + Redundancy",
    "minicheck_only": "MiniCheck Only",
    "minicheck_redundancy": "MiniCheck + Redundancy",
    "summary_level": "Summary-level",
}

DISPLAY_LABELS = {
    "baseline_raw_baseline_raw": "Baseline raw",
    "baseline3_baseline3": "Baseline3",
    "ilp_rouge_only": "ILP",
    "mmr_rouge_only": "MMR",
    "dpp_rouge_only": "DPP",
    "submodular_rouge_only": "Submodular",
    "lns_rouge_only": "LNS",
    "ilp_rouge_redundancy": "ILP",
    "mmr_rouge_redundancy": "MMR",
    "dpp_rouge_redundancy": "DPP",
    "submodular_rouge_redundancy": "Submodular",
    "lns_rouge_redundancy": "LNS",
    "ilp_minicheck_only": "ILP",
    "mmr_minicheck_only": "MMR",
    "dpp_minicheck_only": "DPP",
    "submodular_minicheck_only": "Submodular",
    "lns_minicheck_only": "LNS",
    "ilp_minicheck_redundancy": "ILP",
    "mmr_minicheck_redundancy": "MMR",
    "dpp_minicheck_redundancy": "DPP",
    "submodular_minicheck_redundancy": "Submodular",
    "lns_minicheck_redundancy": "LNS",
    "mbr_summary_mbr": "MBR",
    "pareto_summary_pareto": "Pareto",
}

KNOWN_NAMED_SPLITS = {"train", "validation"}
ROUGE_PRF_RE = re.compile(
    r"^\s*(rouge1|rouge2|rougeL|rougeLsum)\s+Precision=([-\d.]+)%\s+Recall=([-\d.]+)%\s+F1=([-\d.]+)%$"
)
ROUGE_F1_RE = re.compile(r"^\s*(rouge1|rouge2|rougeL|rougeLsum)\s+F1=([-\d.]+)%$")
BERTSCORE_RE = re.compile(r"^\s*Precision=([-\d.]+)%\s+Recall=([-\d.]+)%\s+F1=([-\d.]+)%$")
ENTAILMENT_RE = re.compile(r"^\s*Entailment:\s*([-\d.]+)%$")
FACTCC_RE = re.compile(r"^\s*SentenceAvgCorrect:\s*([-\d.]+)%$")
MINICHECK_RE = re.compile(r"^\s*SummaryAvgConsistent:\s*([-\d.]+)%$")
ALIGNSCORE_RE = re.compile(r"^\s*SummaryAvg:\s*([-\d.]+)%$")
SAMPLES_RE = re.compile(r"^Samples:\s*(\d+)")
BEAM_RE = re.compile(r"^Beam size:\s*(\d+)")
SPLIT_RE = re.compile(r"^Split:\s*(train|validation|test)")
ROUGE_IMPL_RE = re.compile(r"^ROUGE implementation:\s*(.+)$")
BUDGET_RE = re.compile(r"^Budget:\s*(.+)$")


def objective_group(experiment: str) -> str:
    if experiment.startswith("baseline"):
        return "baseline"
    if experiment.startswith("mbr_summary_mbr") or experiment.startswith("pareto_summary_pareto"):
        return "summary_level"
    if experiment.endswith("rouge_only"):
        return "rouge_only"
    if experiment.endswith("rouge_redundancy"):
        return "rouge_redundancy"
    if experiment.endswith("minicheck_only"):
        return "minicheck_only"
    if experiment.endswith("minicheck_redundancy"):
        return "minicheck_redundancy"
    raise ValueError(f"Unknown experiment grouping: {experiment}")


def parse_result_file(path: Path) -> dict[str, float | str | int]:
    row: dict[str, float | str | int] = {
        "experiment": path.parent.name,
        "group": objective_group(path.parent.name),
        "label": DISPLAY_LABELS[path.parent.name],
        "file": str(path),
    }
    lines = path.read_text(encoding="utf-8").splitlines()
    in_bertscore = False

    for line in lines:
        samples_match = SAMPLES_RE.search(line)
        if samples_match:
            row["samples"] = int(samples_match.group(1))
            continue

        beam_match = BEAM_RE.search(line)
        if beam_match:
            row["beam_size"] = int(beam_match.group(1))
            continue

        split_match = SPLIT_RE.search(line)
        if split_match:
            row["split"] = split_match.group(1)
            continue

        rouge_impl_match = ROUGE_IMPL_RE.search(line)
        if rouge_impl_match:
            row["rouge_impl"] = rouge_impl_match.group(1).strip()
            continue

        budget_match = BUDGET_RE.search(line)
        if budget_match:
            row["budget"] = budget_match.group(1).strip()
            continue

        rouge_prf_match = ROUGE_PRF_RE.search(line)
        if rouge_prf_match:
            metric = rouge_prf_match.group(1)
            row[f"{metric}_precision"] = float(rouge_prf_match.group(2))
            row[f"{metric}_recall"] = float(rouge_prf_match.group(3))
            row[f"{metric}_f1"] = float(rouge_prf_match.group(4))
            continue

        rouge_f1_match = ROUGE_F1_RE.search(line)
        if rouge_f1_match:
            metric = rouge_f1_match.group(1)
            row[f"{metric}_f1"] = float(rouge_f1_match.group(2))
            continue

        if line.startswith("BERTScore"):
            in_bertscore = True
            continue

        if in_bertscore:
            bertscore_match = BERTSCORE_RE.search(line)
            if bertscore_match:
                row["bertscore_precision"] = float(bertscore_match.group(1))
                row["bertscore_recall"] = float(bertscore_match.group(2))
                row["bertscore_f1"] = float(bertscore_match.group(3))
                in_bertscore = False
            continue

        entailment_match = ENTAILMENT_RE.search(line)
        if entailment_match:
            row["entailment"] = float(entailment_match.group(1))
            continue

        factcc_match = FACTCC_RE.search(line)
        if factcc_match:
            row["factcc"] = float(factcc_match.group(1))
            continue

        minicheck_match = MINICHECK_RE.search(line)
        if minicheck_match:
            row["minicheck"] = float(minicheck_match.group(1))
            continue

        alignscore_match = ALIGNSCORE_RE.search(line)
        if alignscore_match:
            row["alignscore"] = float(alignscore_match.group(1))
            continue

    return row


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
    if not experiment_dir.exists():
        raise FileNotFoundError(f"Missing experiment directory: {experiment_dir}")

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


def load_rows(results_root: Path, beam_size: int = 5, split: str = "test", rouge_impl: str = "hf") -> list[dict[str, float | str | int]]:
    parsed_rows = []
    for experiment in EXPERIMENT_ORDER:
        result_file = find_result_file(results_root / experiment, beam_size=beam_size, split=split, rouge_impl=rouge_impl)
        parsed_rows.append(parse_result_file(result_file))
    return parsed_rows


def ordered_fieldnames(rows: list[dict[str, float | str | int]]) -> list[str]:
    preferred = [
        "experiment",
        "group",
        "label",
        "samples",
        "beam_size",
        "split",
        "budget",
        "rouge_impl",
        "rouge1_precision",
        "rouge1_recall",
        "rouge1_f1",
        "rouge2_precision",
        "rouge2_recall",
        "rouge2_f1",
        "rougeL_precision",
        "rougeL_recall",
        "rougeL_f1",
        "rougeLsum_precision",
        "rougeLsum_recall",
        "rougeLsum_f1",
        "bertscore_precision",
        "bertscore_recall",
        "bertscore_f1",
        "factcc",
        "minicheck",
        "alignscore",
        "entailment",
        "file",
    ]
    present = {key for row in rows for key in row.keys()}
    ordered = [key for key in preferred if key in present]
    extras = sorted(present.difference(ordered))
    return ordered + extras


def write_csv(rows: list[dict[str, float | str | int]], output_path: Path) -> None:
    fieldnames = ordered_fieldnames(rows)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def add_group_guides(ax: plt.Axes, rows: list[dict[str, float | str | int]]) -> None:
    seen_groups: list[tuple[str, int, int]] = []
    current_group = None
    start_idx = 0

    for idx, row in enumerate(rows):
        group = str(row["group"])
        if current_group is None:
            current_group = group
            start_idx = idx
            continue
        if group != current_group:
            seen_groups.append((current_group, start_idx, idx - 1))
            current_group = group
            start_idx = idx
    seen_groups.append((str(rows[-1]["group"]), start_idx, len(rows) - 1))

    for group, start, end in seen_groups:
        center = (start + end) / 2
        ax.text(
            -0.19,
            center,
            GROUP_TITLES[group],
            transform=ax.get_yaxis_transform(),
            ha="right",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#334155",
        )
        if end < len(rows) - 1:
            ax.axhline(end + 0.5, color="#cbd5e1", linewidth=1.2)


def plot_triplet(
    rows: list[dict[str, float | str | int]],
    metric_prefix: str,
    title: str,
    output_path: Path,
) -> None:
    labels = [str(row["label"]) for row in rows]
    positions = list(range(len(rows)))
    offsets = [0.24, 0.0, -0.24]
    height = 0.22

    fig_height = max(10.5, len(rows) * 0.42)
    fig, ax = plt.subplots(figsize=(14.5, fig_height))

    precision = [float(row[f"{metric_prefix}_precision"]) for row in rows]
    recall = [float(row[f"{metric_prefix}_recall"]) for row in rows]
    f1 = [float(row[f"{metric_prefix}_f1"]) for row in rows]

    ax.barh([pos + offsets[0] for pos in positions], precision, height=height, color="#2563eb", label="Precision")
    ax.barh([pos + offsets[1] for pos in positions], recall, height=height, color="#f97316", label="Recall")
    ax.barh([pos + offsets[2] for pos in positions], f1, height=height, color="#16a34a", label="F1")

    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, max(max(precision), max(recall), max(f1)) + 5)
    ax.set_xlabel("Score (%)")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=16)
    ax.grid(axis="x", linestyle="--", linewidth=0.8, alpha=0.35)
    ax.legend(loc="upper right", frameon=False, ncols=3)
    add_group_guides(ax, rows)
    fig.subplots_adjust(left=0.28, right=0.98, top=0.95, bottom=0.04)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_single_metric(
    rows: list[dict[str, float | str | int]],
    metric_key: str,
    title: str,
    output_path: Path,
    label: str = "F1",
) -> None:
    labels = [str(row["label"]) for row in rows]
    positions = list(range(len(rows)))
    values = [float(row[metric_key]) for row in rows]

    fig_height = max(10.5, len(rows) * 0.42)
    fig, ax = plt.subplots(figsize=(14.5, fig_height))

    ax.barh(positions, values, height=0.5, color="#16a34a", label=label)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, max(values) + 5)
    ax.set_xlabel("Score (%)")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=16)
    ax.grid(axis="x", linestyle="--", linewidth=0.8, alpha=0.35)
    ax.legend(loc="upper right", frameon=False)
    add_group_guides(ax, rows)
    fig.subplots_adjust(left=0.28, right=0.98, top=0.95, bottom=0.04)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_metric(rows: list[dict[str, float | str | int]], metric_prefix: str, title: str, output_path: Path) -> None:
    precision_key = f"{metric_prefix}_precision"
    recall_key = f"{metric_prefix}_recall"
    if all(precision_key in row and recall_key in row for row in rows):
        plot_triplet(rows, metric_prefix, title, output_path)
        return
    plot_single_metric(rows, f"{metric_prefix}_f1", title, output_path, label="F1")


def plot_factuality(rows: list[dict[str, float | str | int]], output_path: Path) -> None:
    labels = [str(row["label"]) for row in rows]
    positions = list(range(len(rows)))
    metric_specs = [
        ("factcc", "FactCC", "#0f766e"),
        ("minicheck", "MiniCheck", "#7c3aed"),
        ("alignscore", "AlignScore", "#ea580c"),
        ("entailment", "Entailment", "#2563eb"),
    ]
    available_specs = [spec for spec in metric_specs if all(spec[0] in row for row in rows)]
    if not available_specs:
        raise ValueError("No factuality metrics available to plot.")

    bar_span = 0.66
    if len(available_specs) == 1:
        offsets = [0.0]
    else:
        step = bar_span / max(1, len(available_specs) - 1)
        start = bar_span / 2
        offsets = [start - idx * step for idx in range(len(available_specs))]
    height = min(0.18, 0.72 / max(1, len(available_specs)))

    fig_height = max(10.5, len(rows) * 0.42)
    fig, ax = plt.subplots(figsize=(14.5, fig_height))

    metric_values: list[list[float]] = []
    for offset, (metric_key, label, color) in zip(offsets, available_specs):
        values = [float(row[metric_key]) for row in rows]
        metric_values.append(values)
        ax.barh([pos + offset for pos in positions], values, height=height, color=color, label=label)

    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, max(max(values) for values in metric_values) + 5)
    ax.set_xlabel("Score (%)")
    ax.set_title("Factuality Metrics by Objective Group", fontsize=15, fontweight="bold", pad=16)
    ax.grid(axis="x", linestyle="--", linewidth=0.8, alpha=0.35)
    ax.legend(loc="upper right", frameon=False, ncols=min(4, len(available_specs)))
    add_group_guides(ax, rows)
    fig.subplots_adjust(left=0.28, right=0.98, top=0.95, bottom=0.04)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_plots(results_root: Path, output_dir: Path, beam_size: int, split: str, rouge_impl: str) -> list[Path]:
    rows = load_rows(results_root, beam_size=beam_size, split=split, rouge_impl=rouge_impl)
    ensure_dir(output_dir)
    write_csv(rows, output_dir / "summary_metrics_full.csv")

    outputs = [
        output_dir / "01_rouge1.png",
        output_dir / "02_rouge2.png",
        output_dir / "03_rougeL.png",
        output_dir / "04_rougeLsum.png",
        output_dir / "05_bertscore.png",
        output_dir / "06_factuality_metrics.png",
    ]
    plot_metric(rows, "rouge1", "ROUGE-1 by Objective Group", outputs[0])
    plot_metric(rows, "rouge2", "ROUGE-2 by Objective Group", outputs[1])
    plot_metric(rows, "rougeL", "ROUGE-L by Objective Group", outputs[2])
    plot_metric(rows, "rougeLsum", "ROUGE-Lsum by Objective Group", outputs[3])
    plot_triplet(rows, "bertscore", "BERTScore Precision / Recall / F1 by Objective Group", outputs[4])
    plot_factuality(rows, outputs[5])
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot grouped evaluation charts from experiment result files.")
    parser.add_argument(
        "--results-root",
        type=Path,
        default=DEFAULT_RESULTS_ROOT,
        help="Directory containing per-experiment result folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_PLOTS_DIR,
        help="Directory where CSV and PNG files will be written.",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Beam size to load from result filenames (default: 5).",
    )
    parser.add_argument(
        "--split",
        choices=["train", "validation", "test"],
        default="test",
        help="Dataset split encoded in result filenames (default: test).",
    )
    parser.add_argument(
        "--rouge-impl",
        choices=["hf", "local"],
        default="hf",
        help="ROUGE variant encoded in result filenames (default: hf).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_paths = build_plots(
        args.results_root,
        args.output_dir,
        beam_size=args.beam_size,
        split=args.split,
        rouge_impl=args.rouge_impl,
    )
    for path in output_paths:
        print(path)


if __name__ == "__main__":
    main()
