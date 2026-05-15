from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRID_CSV = ROOT / "bart" / "results" / "tri_metric_grid_search.csv"
DEFAULT_PNG = ROOT / "bart" / "results" / "tri_metric_pareto.png"
DEFAULT_PDF = ROOT / "bart" / "results" / "tri_metric_pareto.pdf"
DEFAULT_SELECTED_CSV = ROOT / "bart" / "results" / "tri_metric_selected_configs.csv"
DEFAULT_REPORT_MD = ROOT / "bart" / "results" / "tri_metric_vs_existing.md"
DEFAULT_BASELINE_CSV = ROOT / "bart" / "results" / "summary_metrics_beam5_hfrouge.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot tri-metric Pareto fronts and export selected configs.")
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_GRID_CSV)
    parser.add_argument("--output-png", type=Path, default=DEFAULT_PNG)
    parser.add_argument("--output-pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--selected-csv", type=Path, default=DEFAULT_SELECTED_CSV)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--baseline-csv", type=Path, default=DEFAULT_BASELINE_CSV)
    parser.add_argument("--baseline-method", default="baseline3")
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--rouge-impl", choices=["hf", "local"], default="hf")
    parser.add_argument("--max-rouge-drop", type=float, default=2.0)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def safe_float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value in {"", None}:
        return None
    return float(value)


def ensure_baseline_csv(path: Path, beam_size: int, rouge_impl: str) -> Path | None:
    if path.exists():
        return path

    from build_summary_metrics_csv import build_summary_rows, default_output_csv

    try:
        rows = build_summary_rows(ROOT / "bart" / "results", beam_size=beam_size, rouge_impl=rouge_impl)
    except FileNotFoundError:
        return None
    if not rows:
        return None

    output_path = default_output_csv(ROOT / "bart" / "results", beam_size, rouge_impl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def detect_baseline_rouge1(path: Path | None, baseline_method: str) -> float | None:
    if path is None or not path.exists():
        return None
    rows = load_rows(path)
    for row in rows:
        if row.get("Method") != baseline_method:
            continue
        if row.get("Split") != "test":
            continue
        return float(row["ROUGE-1"])
    return None


def pareto_front(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    front = []
    for lhs in rows:
        dominated = False
        for rhs in rows:
            if lhs is rhs:
                continue
            if rhs["ROUGE-1"] >= lhs["ROUGE-1"] and rhs["MiniCheck"] >= lhs["MiniCheck"] and (
                rhs["ROUGE-1"] > lhs["ROUGE-1"] or rhs["MiniCheck"] > lhs["MiniCheck"]
            ):
                dominated = True
                break
        if not dominated:
            front.append(lhs)
    return sorted(front, key=lambda row: row["ROUGE-1"])


def knee_point(front: list[dict[str, float]]) -> dict[str, float] | None:
    if len(front) < 3:
        return front[0] if front else None
    left = front[0]
    right = front[-1]
    dx = right["ROUGE-1"] - left["ROUGE-1"]
    dy = right["MiniCheck"] - left["MiniCheck"]
    norm = (dx ** 2 + dy ** 2) ** 0.5
    if norm == 0:
        return front[0]

    best_row = None
    best_distance = -1.0
    for row in front[1:-1]:
        distance = abs(dy * row["ROUGE-1"] - dx * row["MiniCheck"] + right["ROUGE-1"] * left["MiniCheck"] - right["MiniCheck"] * left["ROUGE-1"]) / norm
        if distance > best_distance:
            best_distance = distance
            best_row = row
    return best_row


def select_candidates(
    rows: list[dict[str, float]],
    rouge_threshold: float | None,
) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
    by_method: dict[str, list[dict[str, float]]] = {}
    for row in rows:
        by_method.setdefault(str(row["method"]), []).append(row)

    selected = []
    knee_rows = []
    for method, method_rows in sorted(by_method.items()):
        method_front = pareto_front(method_rows)
        knee = knee_point(method_front)
        if knee is not None:
            knee_rows.append(knee)

        feasible = (
            [row for row in method_rows if row["ROUGE-1"] >= rouge_threshold]
            if rouge_threshold is not None
            else list(method_rows)
        )
        if feasible:
            best = max(feasible, key=lambda row: (row["MiniCheck"], row["ROUGE-1"]))
        else:
            best = max(method_rows, key=lambda row: (row["ROUGE-1"], row["MiniCheck"]))
        selected.append(best)
    return selected, knee_rows


def write_selected_csv(path: Path, rows: list[dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["method", "w_rouge", "w_minicheck", "w_redundancy", "ROUGE-1", "MiniCheck", "Notes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "method": row["method"],
                    "w_rouge": f"{row['w_rouge']:.2f}",
                    "w_minicheck": f"{row['w_minicheck']:.2f}",
                    "w_redundancy": f"{row['w_redundancy']:.2f}",
                    "ROUGE-1": f"{row['ROUGE-1']:.2f}",
                    "MiniCheck": f"{row['MiniCheck']:.2f}",
                    "Notes": row.get("Notes", ""),
                }
            )


def write_report(
    path: Path,
    baseline_rouge1: float | None,
    rouge_threshold: float | None,
    rows: list[dict[str, float]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Tri-Metric 与现有结果对比",
        "",
        f"- 基线方法：`baseline3`",
        (
            f"- 基线 ROUGE-1：`{baseline_rouge1:.2f}`"
            if baseline_rouge1 is not None
            else "- 基线 ROUGE-1：`不可用`"
        ),
        (
            f"- 约束条件：`ROUGE-1 >= {rouge_threshold:.2f}`"
            if rouge_threshold is not None
            else "- 约束条件：`不可用（缺少基线，因此按 MiniCheck 优先、ROUGE 次优进行筛选）`"
        ),
        "",
        "## 入选配置",
        "",
        "| 方法 | w_rouge | w_minicheck | w_redundancy | ROUGE-1 | MiniCheck | 备注 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['method']} | {row['w_rouge']:.2f} | {row['w_minicheck']:.2f} | {row['w_redundancy']:.2f} | "
            f"{row['ROUGE-1']:.2f} | {row['MiniCheck']:.2f} | {row.get('Notes', '')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    baseline_csv = ensure_baseline_csv(args.baseline_csv, args.beam_size, args.rouge_impl)
    baseline_rouge1 = detect_baseline_rouge1(baseline_csv, args.baseline_method)
    rouge_threshold = None if baseline_rouge1 is None else baseline_rouge1 - args.max_rouge_drop

    rows = []
    for row in load_rows(args.input_csv):
        rouge1 = safe_float(row, "ROUGE-1")
        minicheck = safe_float(row, "MiniCheck")
        if rouge1 is None or minicheck is None:
            continue
        rows.append(
            {
                "method": row["method"],
                "w_rouge": float(row["w_rouge"]),
                "w_minicheck": float(row["w_minicheck"]),
                "w_redundancy": float(row["w_redundancy"]),
                "ROUGE-1": rouge1,
                "MiniCheck": minicheck,
                "Notes": row.get("Notes", ""),
            }
        )

    if not rows:
        raise SystemExit(f"No usable tri-metric rows found in {args.input_csv}")

    selected_rows, knee_rows = select_candidates(rows, rouge_threshold)
    colors = {
        "mmr": "#2563eb",
        "ilp": "#dc2626",
        "lns": "#16a34a",
        "dpp": "#7c3aed",
        "submodular": "#ea580c",
        "mbr": "#0891b2",
        "pareto": "#4f46e5",
    }

    fig, ax = plt.subplots(figsize=(12, 8))
    for method in sorted({row["method"] for row in rows}):
        method_rows = [row for row in rows if row["method"] == method]
        xs = [row["ROUGE-1"] for row in method_rows]
        ys = [row["MiniCheck"] for row in method_rows]
        ax.scatter(xs, ys, s=42, alpha=0.75, color=colors.get(method, "#334155"), label=method)
        front = pareto_front(method_rows)
        ax.plot(
            [row["ROUGE-1"] for row in front],
            [row["MiniCheck"] for row in front],
            color=colors.get(method, "#334155"),
            linewidth=1.5,
            alpha=0.85,
        )

    for row in selected_rows:
        ax.annotate(
            f"{row['method']} ({row['w_rouge']:.1f},{row['w_minicheck']:.1f},{row['w_redundancy']:.1f})",
            (row["ROUGE-1"], row["MiniCheck"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8,
        )
    for row in knee_rows:
        ax.scatter(row["ROUGE-1"], row["MiniCheck"], s=120, facecolors="none", edgecolors="black", linewidths=1.2)

    if rouge_threshold is not None:
        ax.axvline(rouge_threshold, color="#0f172a", linestyle="--", linewidth=1.2, label="ROUGE threshold")
    ax.set_xlabel("ROUGE-1")
    ax.set_ylabel("MiniCheck")
    ax.set_title("Tri-Metric Pareto Frontier by Method")
    ax.legend(loc="best", fontsize=8)
    ax.grid(alpha=0.2)

    args.output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output_png, dpi=220, bbox_inches="tight")
    fig.savefig(args.output_pdf, dpi=220, bbox_inches="tight")
    plt.close(fig)

    write_selected_csv(args.selected_csv, selected_rows)
    write_report(args.report_md, baseline_rouge1, rouge_threshold, selected_rows)

    print(args.output_png)
    print(args.output_pdf)
    print(args.selected_csv)
    print(args.report_md)


if __name__ == "__main__":
    main()
