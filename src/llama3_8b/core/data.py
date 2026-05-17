"""Unified summarization dataset loader for cnn_dailymail and multi_news.

Returns a ``DatasetDict`` whose splits expose the canonical fields used by
the existing pipeline (`article`, `highlights`, `id`). multi_news's
`document` and `summary` are renamed in-place so the orchestration layer
stays unchanged.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from datasets import Dataset, DatasetDict, load_dataset


SUPPORTED_DATASETS = ("cnn_dailymail", "multi_news")


def _load_multi_news_from_stage_outputs() -> DatasetDict:
    """Fallback for environments where HF dataset scripts are disabled.

    The full Llama Multi-News baseline stage output contains the same test
    articles and references in pipeline order, so it is a stable local source
    for resuming selector runs when ``alexfabbri/multi_news`` cannot be loaded.
    """
    root = Path(__file__).resolve().parents[2]
    candidates = []
    env_path = os.environ.get("MULTI_NEWS_STAGE_OUTPUTS_JSONL")
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.extend(
        [
            root
            / "outputs/multi_news/llama3_8b/baseline/full_multi_news_baseline_requested_full_resume_llama_multinews_baseline/baseline_hfrouge_shuffle_seed42_stage_outputs.jsonl",
            root
            / "outputs/multi_news/qwen3_5_9b/baseline/full_multi_news_baseline_requested_full_resume_qwen_multinews_baseline/baseline_hfrouge_shuffle_seed42_stage_outputs.jsonl",
            root
            / "outputs/multi_news/primera_multinews/baseline/full_multi_news_baseline_requested_full_resume_primera_multinews_baseline/beam5_baseline_hfrouge_shuffle_seed42_stage_outputs.jsonl",
        ]
    )
    for candidate in candidates:
        if not candidate.exists():
            continue
        rows = []
        with candidate.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue
                obj = json.loads(line)
                article = obj.get("source_document") if "source_document" in obj else obj.get("article")
                highlights = (
                    obj.get("reference_summary")
                    if "reference_summary" in obj
                    else obj.get("highlights")
                )
                if article is None or highlights is None:
                    raise ValueError(f"missing article/reference fields in {candidate} at row {idx}")
                rows.append(
                    {
                        "article": article,
                        "highlights": highlights,
                        "id": obj.get("id") or f"multi_news_test_{idx}",
                    }
                )
        if rows:
            print(f"[data] loaded Multi-News test split from local stage outputs: {candidate} ({len(rows)} rows)")
            return DatasetDict({"test": Dataset.from_list(rows)})
    raise FileNotFoundError(
        "Could not load alexfabbri/multi_news and no local Multi-News stage output fallback was found."
    )


def _load_multi_news() -> DatasetDict:
    try:
        ds = load_dataset("alexfabbri/multi_news")
    except RuntimeError as exc:
        if "Dataset scripts are no longer supported" not in str(exc):
            raise
        print(f"[data] Hugging Face Multi-News script load failed: {exc}")
        return _load_multi_news_from_stage_outputs()
    result = DatasetDict()
    for split_name, split_ds in ds.items():
        result[split_name] = split_ds.rename_columns(
            {"document": "article", "summary": "highlights"}
        ).map(
            lambda examples, indices: {"id": [f"multi_news_{split_name}_{idx}" for idx in indices]},
            with_indices=True,
            batched=True,
        )
    return result


def load_summarization_dataset(name: str) -> DatasetDict:
    if name == "cnn_dailymail":
        return load_dataset("cnn_dailymail", "3.0.0")
    if name == "multi_news":
        return _load_multi_news()
    raise ValueError(
        f"unknown dataset: {name!r}. supported: {SUPPORTED_DATASETS}"
    )
