"""Helpers for running FACTGRAPH factuality scoring via its official evaluate.sh.

FACTGRAPH (https://github.com/amazon-science/fact-graph) operates at sentence
level. We split each generated summary into sentences with the pysbd segmenter
(same protocol as FactCC/MiniCheck), pair each sentence with the full article,
invoke the official ``evaluate.sh <mode> <jsonl> <gpu_id>`` as a subprocess,
then average per-sentence scores back to a per-summary score (0..1).

Configure the FACTGRAPH repo location via:
    - env var FACTGRAPH_REPO_DIR (preferred), or
    - explicit ``repo_dir`` argument to load_factgraph_config().

This is a wrapper only — no FACTGRAPH logic is re-implemented here.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


FACTGRAPH_REPO_DIR_ENV = "FACTGRAPH_REPO_DIR"
FACTGRAPH_GPU_ID_ENV = "FACTGRAPH_GPU_ID"
FACTGRAPH_MODE_ENV = "FACTGRAPH_MODE"

FACTGRAPH_SCORE_KEYS = (
    "factgraph_score",
    "score",
    "prob",
    "probability",
    "pred_prob",
    "factual_prob",
)
FACTGRAPH_LABEL_KEYS = (
    "factgraph_label",
    "label",
    "prediction",
    "pred",
    "pred_label",
)
FACTGRAPH_FACTUAL_STRINGS = {"factual", "correct", "entailment", "1", "true"}
FACTGRAPH_NONFACTUAL_STRINGS = {
    "non_factual",
    "nonfactual",
    "incorrect",
    "contradiction",
    "0",
    "false",
}


@dataclass
class FactGraphConfig:
    repo_dir: Path
    evaluate_sh: Path
    mode: str
    gpu_id: int


def load_factgraph_config(
    repo_dir: str | os.PathLike | None = None,
    mode: str | None = None,
    gpu_id: int | None = None,
) -> FactGraphConfig:
    """Validate the official FACTGRAPH install and return a run config.

    Resolution order for repo_dir / mode / gpu_id: explicit arg > env var >
    default. Raises FileNotFoundError / PermissionError with a clear message if
    the install is missing or evaluate.sh is not executable.
    """
    repo_dir = repo_dir if repo_dir is not None else os.environ.get(FACTGRAPH_REPO_DIR_ENV)
    if not repo_dir:
        raise FileNotFoundError(
            f"FACTGRAPH repo dir not configured. Set ${FACTGRAPH_REPO_DIR_ENV} or pass repo_dir "
            "explicitly. Clone https://github.com/amazon-science/fact-graph first."
        )
    repo_path = Path(repo_dir).expanduser().resolve()
    if not repo_path.is_dir():
        raise FileNotFoundError(f"FACTGRAPH repo dir is not a directory: {repo_path}")

    candidate_scripts = [repo_path / "evaluate.sh", repo_path / "src" / "evaluate.sh"]
    evaluate_sh = None
    for candidate in candidate_scripts:
        if candidate.exists():
            evaluate_sh = candidate
            break
    if evaluate_sh is None:
        raise FileNotFoundError(
            "evaluate.sh not found in the FACTGRAPH repo. Checked: "
            + ", ".join(str(path) for path in candidate_scripts)
        )
    if not os.access(evaluate_sh, os.X_OK):
        raise PermissionError(
            f"{evaluate_sh} is not executable. Run `chmod +x {evaluate_sh}` first."
        )

    if mode is None:
        mode = os.environ.get(FACTGRAPH_MODE_ENV, "factgraph")
    if gpu_id is None:
        env_gpu = os.environ.get(FACTGRAPH_GPU_ID_ENV)
        gpu_id = int(env_gpu) if env_gpu is not None and env_gpu != "" else 0

    return FactGraphConfig(repo_dir=repo_path, evaluate_sh=evaluate_sh.resolve(), mode=mode, gpu_id=int(gpu_id))


def _split_summary_sentences(summary: str, segmenter) -> list[str]:
    sentences = [s.strip() for s in segmenter.segment(summary) if s and s.strip()]
    if not sentences and summary.strip():
        sentences = [summary.strip()]
    return sentences


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} is not valid JSON: {exc}") from exc
    return rows


def _first_float(row: dict[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        if key in row and row[key] is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                continue
    return None


def _first_label(row: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _label_to_factual_float(label: Any) -> float | None:
    if label is None:
        return None
    if isinstance(label, bool):
        return 1.0 if label else 0.0
    if isinstance(label, (int, float)):
        return float(label)
    if isinstance(label, str):
        normalized = label.strip().lower()
        if normalized in FACTGRAPH_FACTUAL_STRINGS:
            return 1.0
        if normalized in FACTGRAPH_NONFACTUAL_STRINGS:
            return 0.0
    return None


def _candidate_output_paths(repo_dir: Path, input_jsonl: Path) -> list[Path]:
    stem = input_jsonl.stem
    input_parent = input_jsonl.parent
    candidates: list[Path] = []
    for base in (
        input_parent,
        repo_dir,
        repo_dir / "output",
        repo_dir / "outputs",
        repo_dir / "results",
    ):
        for name in (
            f"{stem}.pred.jsonl",
            f"{stem}.scored.jsonl",
            f"{stem}.factgraph.jsonl",
            f"{stem}_pred.jsonl",
            f"{stem}_scored.jsonl",
            f"{stem}_predictions.jsonl",
            "predictions.jsonl",
            "pred.jsonl",
            f"{stem}.out.jsonl",
        ):
            candidate = base / name
            if candidate not in candidates:
                candidates.append(candidate)
    candidates.append(input_jsonl)
    return candidates


def _locate_factgraph_output(repo_dir: Path, input_jsonl: Path) -> tuple[Path, list[dict[str, Any]]]:
    for candidate in _candidate_output_paths(repo_dir, input_jsonl):
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            rows = _read_jsonl(candidate)
        except ValueError:
            continue
        if not rows:
            continue
        has_score = any(_first_float(r, FACTGRAPH_SCORE_KEYS) is not None for r in rows)
        has_label = any(_first_label(r, FACTGRAPH_LABEL_KEYS) is not None for r in rows)
        if has_score or has_label:
            return candidate, rows
    raise FileNotFoundError(
        "Could not locate FACTGRAPH output with score/label fields. Check the FACTGRAPH repo "
        "after the subprocess exits, or set FACTGRAPH_OUTPUT_PATH to its absolute path."
    )


def _align_scores(
    sentence_records: list[dict[str, Any]],
    output_rows: list[dict[str, Any]],
    output_path: Path,
) -> tuple[list[float | None], list[Any]]:
    scores: list[float | None] = [None] * len(sentence_records)
    labels: list[Any] = [None] * len(sentence_records)

    keyed: dict[tuple[int, int], dict[str, Any]] = {}
    for row in output_rows:
        if "idx" in row and "sent_idx" in row:
            try:
                keyed[(int(row["idx"]), int(row["sent_idx"]))] = row
            except (TypeError, ValueError):
                continue

    if keyed and len(keyed) >= len(sentence_records) * 0.5:
        for i, rec in enumerate(sentence_records):
            row = keyed.get((int(rec["idx"]), int(rec["sent_idx"])))
            if row is None:
                continue
            scores[i] = _first_float(row, FACTGRAPH_SCORE_KEYS)
            labels[i] = _first_label(row, FACTGRAPH_LABEL_KEYS)
        return scores, labels

    if len(output_rows) != len(sentence_records):
        raise ValueError(
            f"FACTGRAPH output at {output_path} has {len(output_rows)} rows but wrapper produced "
            f"{len(sentence_records)} sentence inputs. Cannot align by order; set "
            "FACTGRAPH_OUTPUT_PATH or patch evaluate.sh to pass idx+sent_idx through."
        )
    for i, row in enumerate(output_rows):
        scores[i] = _first_float(row, FACTGRAPH_SCORE_KEYS)
        labels[i] = _first_label(row, FACTGRAPH_LABEL_KEYS)
    return scores, labels


def compute_factgraph_summary_scores(
    generated_summaries: Iterable[str],
    articles: Iterable[str],
    config: FactGraphConfig,
    segmenter,
    workdir: str | os.PathLike | None = None,
    explicit_output_path: str | os.PathLike | None = None,
) -> list[float]:
    """Run FACTGRAPH on per-sentence inputs and return one score per summary.

    Sentences that FACTGRAPH does not emit a usable value for are dropped from
    that summary's aggregate. Summaries with zero usable sentences fall back
    to 0.0 so downstream averaging does not explode.
    """
    generated_summaries = list(generated_summaries)
    articles = list(articles)
    if len(generated_summaries) != len(articles):
        raise ValueError(
            f"generated_summaries ({len(generated_summaries)}) and articles ({len(articles)}) "
            "must be the same length."
        )

    cleanup = False
    if workdir is None:
        workdir_path = Path(tempfile.mkdtemp(prefix="factgraph_eval_"))
        cleanup = True
    else:
        workdir_path = Path(workdir)
        workdir_path.mkdir(parents=True, exist_ok=True)

    try:
        sentence_records: list[dict[str, Any]] = []
        jsonl_rows: list[dict[str, Any]] = []
        for idx, (summary, article) in enumerate(zip(generated_summaries, articles)):
            article_str = str(article)
            sentences = _split_summary_sentences(str(summary), segmenter)
            for sent_idx, sentence in enumerate(sentences):
                record = {"idx": idx, "sent_idx": sent_idx}
                sentence_records.append(record)
                jsonl_rows.append({**record, "summary": sentence, "article": article_str})

        if not jsonl_rows:
            return [0.0] * len(generated_summaries)

        input_jsonl = workdir_path / "factgraph_input.jsonl"
        _write_jsonl(input_jsonl, jsonl_rows)

        cmd = [str(config.evaluate_sh), config.mode, str(input_jsonl.resolve()), str(config.gpu_id)]
        run_cwd = config.evaluate_sh.parent
        print(f"  [factgraph] running: {' '.join(cmd)} (cwd={run_cwd})")
        process = subprocess.run(
            cmd,
            cwd=str(run_cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        log_path = workdir_path / "factgraph_run.log"
        log_path.write_text(process.stdout or "", encoding="utf-8")
        if process.returncode != 0:
            tail = "\n".join((process.stdout or "").splitlines()[-40:])
            raise RuntimeError(
                f"FACTGRAPH evaluate.sh exited with code {process.returncode}.\n"
                f"Log: {log_path}\nLast lines:\n{tail}"
            )

        if explicit_output_path:
            output_path = Path(explicit_output_path)
            output_rows = _read_jsonl(output_path)
        else:
            output_path, output_rows = _locate_factgraph_output(config.repo_dir, input_jsonl)
        print(f"  [factgraph] parsed scores from {output_path}")

        sent_scores, sent_labels = _align_scores(sentence_records, output_rows, output_path)

        summary_scores: list[float] = [0.0] * len(generated_summaries)
        bucket: dict[int, list[float]] = {i: [] for i in range(len(generated_summaries))}
        for rec, score, label in zip(sentence_records, sent_scores, sent_labels):
            value = score if score is not None else _label_to_factual_float(label)
            if value is None:
                continue
            bucket[int(rec["idx"])].append(float(value))
        for idx, values in bucket.items():
            if values:
                summary_scores[idx] = sum(values) / len(values)
        return summary_scores
    finally:
        if cleanup:
            try:
                for child in workdir_path.iterdir():
                    try:
                        child.unlink()
                    except OSError:
                        pass
                workdir_path.rmdir()
            except OSError:
                pass
