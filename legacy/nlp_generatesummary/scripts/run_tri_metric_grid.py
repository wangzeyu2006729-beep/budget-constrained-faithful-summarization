from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BART_ROOT = ROOT / "bart"
DEFAULT_OUTPUT_CSV = ROOT / "bart" / "results" / "tri_metric_grid_search.csv"
DEFAULT_RUN_ROOT = ROOT / "bart" / "results" / "tri_metric_grid_runs"
DEFAULT_METHODS = ["mmr", "ilp", "lns", "dpp", "submodular", "mbr", "pareto"]
DEFAULT_PAPER_METRICS = ["rouge", "bertscore"]
DEFAULT_EXTRA_METRICS = ["minicheck", "factcc"]

if str(BART_ROOT) not in sys.path:
    sys.path.insert(0, str(BART_ROOT))

from core.orchestration import run_experiment


FIELDNAMES = [
    "method",
    "w_rouge",
    "w_minicheck",
    "w_redundancy",
    "effective_w_rouge",
    "effective_w_minicheck",
    "effective_w_redundancy",
    "ROUGE-1",
    "ROUGE-2",
    "ROUGE-L",
    "BERTScore_F1",
    "MiniCheck",
    "FactCC",
    "Runtime_sec",
    "Split",
    "NumSamples",
    "Notes",
    "ResultFile",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tri-metric grid search across all BART optimization methods.")
    parser.add_argument("--methods", nargs="+", default=DEFAULT_METHODS, help="Methods to evaluate.")
    parser.add_argument("--split", default="test", choices=["train", "validation", "test"])
    parser.add_argument("--num-samples", type=int, default=50, help="Subset size for each grid run.")
    parser.add_argument("--sample-mode", default="shuffle", choices=["head", "shuffle"])
    parser.add_argument("--sample-seed", type=int, default=42)
    parser.add_argument("--beam-size", type=int, default=5)
    parser.add_argument("--weight-step", type=float, default=0.1, help="Triangular grid step size.")
    parser.add_argument("--weights-file", type=Path, default=None, help="Optional CSV/JSON with explicit weight rows.")
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--resume", action="store_true", help="Skip rows already present in the output CSV.")
    parser.add_argument("--smoke", action="store_true", help="Run only a tiny subset of methods/weights.")
    parser.add_argument("--max-runs", type=int, default=0, help="Hard limit on number of runs (0 = no limit).")
    parser.add_argument("--compute-dtype", choices=["auto", "fp32", "fp16", "bf16"], default="fp32")
    parser.add_argument("--generation-batch-size", type=int, default=None)
    parser.add_argument("--utility-batch-size", type=int, default=None)
    parser.add_argument("--eval-batch-size", type=int, default=None)
    parser.add_argument("--paper-metrics", nargs="+", default=DEFAULT_PAPER_METRICS)
    parser.add_argument("--extra-metrics", nargs="+", default=DEFAULT_EXTRA_METRICS)
    parser.add_argument("--use-local-rouge", action="store_true")
    parser.add_argument("--rouge-only-eval", action="store_true")
    return parser.parse_args()


def _float_tag(value: float) -> str:
    return f"{value:.2f}".replace(".", "p")


def _result_metric(metrics: dict, key: str) -> str:
    totals = metrics.get("rouge_totals")
    if totals is None:
        rouge_scores = metrics.get("rouge_scores", {})
        value = rouge_scores.get(key)
        return "" if value is None else f"{float(value):.2f}"
    return f"{totals[key][2] / max(1, len(metrics.get('rouge_scores', {})) or 1):.2f}"


def _resolve_rouge_value(metrics: dict, key: str, num_samples: int) -> str:
    totals = metrics.get("rouge_totals")
    if totals is None:
        rouge_scores = metrics.get("rouge_scores", {})
        value = rouge_scores.get(key)
        return "" if value is None else f"{float(value):.2f}"
    return f"{totals[key][2] / max(1, num_samples) * 100:.2f}"


def _resolve_metric_value(metrics: dict, key: str) -> str:
    value = metrics.get(key)
    if value is None:
        return ""
    return f"{float(value):.2f}"


def _existing_keys(csv_path: Path) -> set[tuple[str, str, str, str, str, str]]:
    if not csv_path.exists():
        return set()
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return {
            (
                row["method"],
                row["w_rouge"],
                row["w_minicheck"],
                row["w_redundancy"],
                row["Split"],
                row["NumSamples"],
            )
            for row in reader
        }


def _ensure_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()


def _append_row(path: Path, row: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writerow(row)


def build_triangular_grid(step: float) -> list[dict[str, float]]:
    denominator = int(round(1.0 / step))
    if not math.isclose(denominator * step, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise ValueError(f"weight_step={step} is not supported; use a clean divisor of 1.0 such as 0.1.")
    rows = []
    for rouge_idx in range(denominator + 1):
        for minicheck_idx in range(denominator + 1 - rouge_idx):
            redundancy_idx = denominator - rouge_idx - minicheck_idx
            rows.append(
                {
                    "w_rouge": round(rouge_idx * step, 10),
                    "w_minicheck": round(minicheck_idx * step, 10),
                    "w_redundancy": round(redundancy_idx * step, 10),
                }
            )
    return rows


def load_weight_rows(path: Path) -> list[dict[str, float | str]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("rows", [])
        return list(payload)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "method": row.get("method", "").strip() or None,
                    "w_rouge": float(row["w_rouge"]),
                    "w_minicheck": float(row["w_minicheck"]),
                    "w_redundancy": float(row["w_redundancy"]),
                }
            )
        return rows


def build_run_plan(args: argparse.Namespace) -> list[dict[str, float | str]]:
    if args.weights_file is not None:
        weight_rows = load_weight_rows(args.weights_file)
    else:
        weight_rows = build_triangular_grid(args.weight_step)

    methods = list(args.methods)
    if args.smoke:
        methods = methods[: min(3, len(methods))]

    plan = []
    for method in methods:
        if args.smoke:
            matching_rows = [
                row for row in weight_rows if (not row.get("method")) or row.get("method") == method
            ]
            matching_rows = matching_rows[: min(3, len(matching_rows))]
        else:
            matching_rows = weight_rows
        for row in matching_rows:
            row_method = row.get("method")
            if row_method and row_method != method:
                continue
            plan.append(
                {
                    "method": method,
                    "w_rouge": float(row["w_rouge"]),
                    "w_minicheck": float(row["w_minicheck"]),
                    "w_redundancy": float(row["w_redundancy"]),
                }
            )
    if args.max_runs > 0:
        plan = plan[: args.max_runs]
    return plan


def method_note(method: str, weights: dict[str, float]) -> str:
    if method == "mbr":
        return "MBR uses consensus as the ROUGE-side proxy and applies summary-level redundancy as a penalty."
    if method == "mmr":
        return f"MMR maps redundancy to lambda={1.0 - weights['w_redundancy']:.4f}."
    if method in {"ilp", "lns"}:
        threshold = 0.8 - 0.4 * weights["w_redundancy"]
        extra = ""
        if method == "lns":
            extra = f" objective alpha={weights['w_redundancy']:.4f}."
        return f"{method.upper()} maps redundancy to threshold={threshold:.4f}.{extra}"
    if method in {"dpp", "submodular"}:
        return f"{method.upper()} scales off-diagonal similarity by redundancy weight."
    if method == "pareto":
        return "Pareto tri-metric mode uses weighted scalarization."
    return ""


def run_single_config(args: argparse.Namespace, config: dict[str, float | str]) -> dict[str, str]:
    method = str(config["method"])
    w_rouge = float(config["w_rouge"])
    w_minicheck = float(config["w_minicheck"])
    w_redundancy = float(config["w_redundancy"])

    output_dir = args.run_root / method / (
        f"wr{_float_tag(w_rouge)}_wm{_float_tag(w_minicheck)}_wd{_float_tag(w_redundancy)}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = run_experiment(
        Namespace(
            method=method,
            objective=None,
            output_dir=str(output_dir),
            num_samples=args.num_samples,
            sample_mode=args.sample_mode,
            sample_seed=args.sample_seed,
            beam_size=args.beam_size,
            split=args.split,
            use_local_rouge=args.use_local_rouge,
            rouge_only_eval=args.rouge_only_eval,
            generation_batch_size=args.generation_batch_size,
            utility_batch_size=args.utility_batch_size,
            eval_batch_size=args.eval_batch_size,
            compute_dtype=args.compute_dtype,
            tri_metric=True,
            w_rouge=w_rouge,
            w_minicheck=w_minicheck,
            w_redundancy=w_redundancy,
            paper_metric_names=list(args.paper_metrics),
            extra_metric_names=list(args.extra_metrics),
            return_payload=True,
        )
    )

    metrics = payload["metrics"]
    effective_weights = payload.get("tri_metric_weights") or {
        "rouge": w_rouge,
        "minicheck": w_minicheck,
        "redundancy": w_redundancy,
    }
    return {
        "method": method,
        "w_rouge": f"{w_rouge:.2f}",
        "w_minicheck": f"{w_minicheck:.2f}",
        "w_redundancy": f"{w_redundancy:.2f}",
        "effective_w_rouge": f"{effective_weights['rouge']:.4f}",
        "effective_w_minicheck": f"{effective_weights['minicheck']:.4f}",
        "effective_w_redundancy": f"{effective_weights['redundancy']:.4f}",
        "ROUGE-1": _resolve_rouge_value(metrics, "rouge1", payload["num_samples"]),
        "ROUGE-2": _resolve_rouge_value(metrics, "rouge2", payload["num_samples"]),
        "ROUGE-L": _resolve_rouge_value(metrics, "rougeL", payload["num_samples"]),
        "BERTScore_F1": _resolve_metric_value(metrics, "bert_F"),
        "MiniCheck": _resolve_metric_value(metrics, "minicheck"),
        "FactCC": _resolve_metric_value(metrics, "factcc"),
        "Runtime_sec": f"{float(payload['runtime_seconds']):.2f}",
        "Split": args.split,
        "NumSamples": str(payload["num_samples"]),
        "Notes": method_note(method, {"w_rouge": w_rouge, "w_minicheck": w_minicheck, "w_redundancy": w_redundancy}),
        "ResultFile": str(payload["result_file"]),
    }


def main() -> None:
    args = parse_args()
    _ensure_csv(args.output_csv)
    existing = _existing_keys(args.output_csv) if args.resume else set()
    plan = build_run_plan(args)
    print(f"Planned runs: {len(plan)}")

    completed = 0
    for run_index, config in enumerate(plan, start=1):
        key = (
            str(config["method"]),
            f"{float(config['w_rouge']):.2f}",
            f"{float(config['w_minicheck']):.2f}",
            f"{float(config['w_redundancy']):.2f}",
            args.split,
            str(args.num_samples),
        )
        if key in existing:
            print(f"[{run_index}/{len(plan)}] skip existing {key}")
            continue

        print(
            f"[{run_index}/{len(plan)}] run method={config['method']} "
            f"weights=({config['w_rouge']:.2f}, {config['w_minicheck']:.2f}, {config['w_redundancy']:.2f})"
        )
        row = run_single_config(args, config)
        _append_row(args.output_csv, row)
        existing.add(key)
        completed += 1
        print(f"  wrote {args.output_csv}")

    print(f"Completed new runs: {completed}")
    print(args.output_csv)


if __name__ == "__main__":
    main()
