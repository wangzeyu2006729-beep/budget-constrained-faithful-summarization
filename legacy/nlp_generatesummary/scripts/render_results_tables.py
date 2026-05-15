from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_results_by_objective import GROUP_TITLES, load_rows, write_csv


GROUP_ORDER = [
    "baseline",
    "rouge_only",
    "rouge_redundancy",
    "minicheck_only",
    "minicheck_redundancy",
    "summary_level",
]

GROUP_FILE_NAMES = {
    "baseline": "00_baselines_table.png",
    "rouge_only": "01_rouge_only_table.png",
    "rouge_redundancy": "02_rouge_redundancy_table.png",
    "minicheck_only": "03_minicheck_only_table.png",
    "minicheck_redundancy": "04_minicheck_redundancy_table.png",
    "summary_level": "05_summary_level_table.png",
}

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_ROOT = ROOT / "bart" / "results"
DEFAULT_TABLES_DIR = DEFAULT_RESULTS_ROOT / "tables"


def build_columns(rows: list[dict[str, object]]) -> list[tuple[str, str]]:
    has_rouge_triplets = all(
        all(f"{metric}_{field}" in row for field in ("precision", "recall"))
        for row in rows
        for metric in ("rouge1", "rouge2", "rougeL")
    )

    columns = [("Method", "label")]
    if has_rouge_triplets:
        columns.extend(
            [
                ("R1-P", "rouge1_precision"),
                ("R1-R", "rouge1_recall"),
                ("R1-F1", "rouge1_f1"),
                ("R2-P", "rouge2_precision"),
                ("R2-R", "rouge2_recall"),
                ("R2-F1", "rouge2_f1"),
                ("RL-P", "rougeL_precision"),
                ("RL-R", "rougeL_recall"),
                ("RL-F1", "rougeL_f1"),
                ("RLSum-F1", "rougeLsum_f1"),
            ]
        )
    else:
        columns.extend(
            [
                ("R1-F1", "rouge1_f1"),
                ("R2-F1", "rouge2_f1"),
                ("RL-F1", "rougeL_f1"),
                ("RLSum-F1", "rougeLsum_f1"),
            ]
        )

    columns.extend(
        [
            ("BS-P", "bertscore_precision"),
            ("BS-R", "bertscore_recall"),
            ("BS-F1", "bertscore_f1"),
        ]
    )
    for title, key in (
        ("FactCC", "factcc"),
        ("MiniCheck", "minicheck"),
        ("AlignScore", "alignscore"),
        ("Entailment", "entailment"),
    ):
        if all(key in row for row in rows):
            columns.append((title, key))
    return columns


def format_cell(value: object, key: str) -> str:
    if key == "label":
        return str(value)
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return str(value)


def build_group_tables(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {group: [] for group in GROUP_ORDER}
    for row in rows:
        grouped[str(row["group"])].append(row)
    return grouped


def render_table(group: str, rows: list[dict[str, object]], columns: list[tuple[str, str]], output_path: Path) -> None:
    cell_text = [[format_cell(row[key], key) for _, key in columns] for row in rows]
    col_labels = [title for title, _ in columns]

    fig_height = max(2.6, 0.78 * (len(rows) + 2))
    fig, ax = plt.subplots(figsize=(22, fig_height))
    ax.axis("off")

    title = GROUP_TITLES[group]
    ax.text(
        0.5,
        1.06,
        f"{title} Results",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=16,
        fontweight="bold",
    )

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.5)

    header_color = "#dbeafe"
    body_color = "#f8fafc"
    edge_color = "#cbd5e1"
    alt_color = "#eef2ff"

    for (row_idx, col_idx), cell in table.get_celld().items():
        cell.set_edgecolor(edge_color)
        if row_idx == 0:
            cell.set_facecolor(header_color)
            cell.set_text_props(fontweight="bold", color="#0f172a")
        else:
            cell.set_facecolor(body_color if row_idx % 2 else alt_color)
            if col_idx == 0:
                cell.set_text_props(fontweight="bold", color="#1e293b")

    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.04)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render grouped numeric result tables as PNG files.")
    parser.add_argument(
        "--results-root",
        type=Path,
        default=DEFAULT_RESULTS_ROOT,
        help="Directory containing per-experiment result folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_TABLES_DIR,
        help="Directory where table images and CSV will be written.",
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
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(args.results_root, beam_size=args.beam_size, split=args.split, rouge_impl=args.rouge_impl)
    write_csv(rows, args.output_dir / "summary_metrics_full.csv")

    grouped = build_group_tables(rows)
    for group in GROUP_ORDER:
        output_path = args.output_dir / GROUP_FILE_NAMES[group]
        columns = build_columns(grouped[group])
        render_table(group, grouped[group], columns, output_path)
        print(output_path)


if __name__ == "__main__":
    main()
