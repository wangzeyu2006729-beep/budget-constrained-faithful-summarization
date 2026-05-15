from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

import pysbd
import torch

ROOT = Path(__file__).resolve().parents[1]
BART_ROOT = ROOT / "bart"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BART_ROOT) not in sys.path:
    sys.path.insert(0, str(BART_ROOT))

from bart.metrics.evaluation import run_all_evaluations
from bart.output.result_saver import save_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resume evaluation from a *_progress_summaries.jsonl checkpoint without regenerating summaries."
    )
    parser.add_argument("--progress-json", type=Path, required=True)
    parser.add_argument("--progress-jsonl", type=Path, required=True)
    parser.add_argument("--result-file", type=Path, required=True)
    parser.add_argument("--method", required=True)
    parser.add_argument("--objective-desc", required=True)
    parser.add_argument("--split", required=True, choices=["train", "validation", "test"])
    parser.add_argument("--sample-mode", required=True, choices=["head", "shuffle"])
    parser.add_argument("--sample-seed", type=int, required=True)
    parser.add_argument("--beam-size", type=int, required=True)
    parser.add_argument("--budget-desc", required=True)
    parser.add_argument("--eval-suite", default="full", choices=["full", "rouge_only"])
    parser.add_argument("--rouge-impl", default="huggingface_evaluate")
    parser.add_argument("--sentence-split-for-rouge", default="pysbd")
    parser.add_argument("--compute-dtype-desc", default="bf16")
    parser.add_argument("--generation-batch-size", type=int, default=12)
    parser.add_argument("--utility-batch-size", type=int, default=128)
    parser.add_argument("--eval-batch-size", type=int, default=64)
    parser.add_argument("--paper-metrics", nargs="*", default=["rouge", "bertscore"])
    parser.add_argument(
        "--extra-metrics",
        nargs="*",
        default=["factcc", "minicheck", "alignscore", "factgraph", "factkb"],
    )
    return parser.parse_args()


def load_progress_rows(progress_jsonl: Path):
    articles = []
    references = []
    summaries = []
    with progress_jsonl.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            articles.append(row["article"])
            references.append(row["reference"])
            summaries.append(row["summary"])
    return articles, references, summaries


def main() -> None:
    args = parse_args()

    checkpoint = json.loads(args.progress_json.read_text(encoding="utf-8"))
    articles, references, generated_summaries = load_progress_rows(args.progress_jsonl)
    num_samples = len(generated_summaries)
    if num_samples == 0:
        raise SystemExit(f"No rows found in {args.progress_jsonl}")

    if checkpoint.get("samples_completed") != num_samples:
        print(
            "Warning: progress json and jsonl count differ: "
            f"{checkpoint.get('samples_completed')} vs {num_samples}"
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    segmenter = pysbd.Segmenter(language="en", clean=False)

    started_at = perf_counter()
    metrics = run_all_evaluations(
        generated_summaries,
        articles,
        references,
        device,
        segmenter,
        num_samples,
        rouge_impl="hf" if args.rouge_impl == "huggingface_evaluate" else "local",
        eval_suite=args.eval_suite,
        paper_metric_names=list(args.paper_metrics),
        extra_metric_names=list(args.extra_metrics),
        sentence_split_for_rouge=args.sentence_split_for_rouge,
        eval_batch_size=args.eval_batch_size,
    )
    runtime_seconds = perf_counter() - started_at
    metrics["runtime"] = {
        "started_at": None,
        "finished_at": None,
        "total_seconds": round(runtime_seconds, 2),
        "generation_seconds": round(float(checkpoint.get("gen_seconds_so_far", 0.0)), 2),
        "evaluation_seconds": round(runtime_seconds, 2),
        "resumed": True,
        "resumed_from": int(num_samples),
        "prior_generation_seconds": round(float(checkpoint.get("gen_seconds_so_far", 0.0)), 2),
    }

    config_header = (
        f"BART Beam-{args.beam_size} + {args.method.upper()} Summarization Results (Resume-Eval)\n"
        f"Method: {args.method}\n"
        f"Objective variant: {args.objective_desc}\n"
        f"Dataset: cnn_dailymail (3.0.0)\n"
        f"Split: {args.split}\n"
        f"Samples: {num_samples}\n"
        f"Sample mode: {args.sample_mode}\n"
        f"Sample seed: {args.sample_seed}\n"
        f"Beam size: {args.beam_size}\n"
        f"Budget: {args.budget_desc}\n"
        f"Runtime generation batch size: {args.generation_batch_size}\n"
        f"Runtime utility batch size: {args.utility_batch_size}\n"
        f"Runtime eval batch size: {args.eval_batch_size}\n"
        f"Runtime dtype: {args.compute_dtype_desc}\n"
        f"Runtime total seconds: {runtime_seconds:.2f}\n"
        f"Eval suite: {args.eval_suite}\n"
        f"ROUGE implementation: {args.rouge_impl}\n"
        "Recovered from progress_summaries checkpoint.\n"
    )

    args.result_file.parent.mkdir(parents=True, exist_ok=True)
    save_results(str(args.result_file), metrics, generated_summaries, references, config_header, all_sample_logs=None)
    print(f"Wrote resumed result file: {args.result_file}")


if __name__ == "__main__":
    main()
