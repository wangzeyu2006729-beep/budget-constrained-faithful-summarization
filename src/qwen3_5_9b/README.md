# Qwen3.5-9B experiment entrypoints

This folder is the Qwen-side entrypoint and implementation folder. It now carries its own copy of the shared candidate-pool, CO, ordering, trace, and evaluation modules (`core/`, `metrics/`, `opt_selectors/`, `output/`, etc.), so Qwen runs no longer import those modules from `1_bart/`.

Qwen outputs are stored under `1_qwen3.5_9B/results/`. The copied implementation mirrors the BART implementation at the time it was split; keep future shared fixes synchronized in both `1_bart/` and `1_qwen3.5_9B/` when they affect common CO/evaluation behavior.
By default, the Qwen entrypoints run the full requested split (`NUM_SAMPLES=0` means no test-set truncation). Set `NUM_SAMPLES=500` for the smaller shuffled smoke run.

Use `scripts/run_live.sh` from the project root for real-time logs.

```bash
scripts/run_live.sh --name qwen_baseline -- \
  bash 1_qwen3.5_9B/run_baseline.sh

scripts/run_live.sh --name qwen_methods -- \
  bash 1_qwen3.5_9B/run_methods.sh

scripts/run_live.sh --name qwen_full_test_queue -- \
  bash scripts/run_qwen_full_test_queue.sh
```

Method-specific folders are also available:

- `ilp/1_bart/run.sh`
- `ilp/1_qwen3.5_9B/run.sh`
- `dpp/1_bart/run.sh`
- `dpp/1_qwen3.5_9B/run.sh`
- `mmr/1_bart/run.sh`
- `mmr/1_qwen3.5_9B/run.sh`

## Prompt policy

Baseline and CO candidate generation use the same dataset-specific summary-only prompt.

CNN/DailyMail:

```text
Summarize the following news article in English in 3-5 concise sentences.

Output only the summary text.
Do not include a title, label, bullet points, markdown, explanation, preface, or closing note.

Article:
{article}

Summary:
```

Prompt version: `concise_summary_only_v1`.

Multi-News uses `multi_news_concise_summary_only_v1` and changes the article label to `Articles:` with one extra instruction to synthesize shared facts across the documents without repetition.

Baseline uses the official non-thinking general-task Qwen defaults: `GENERATION_DO_SAMPLE=true`, `MAX_GENERATION_NEW_TOKENS=32768`, `GENERATION_TEMPERATURE=0.7`, `GENERATION_TOP_P=0.8`, `GENERATION_TOP_K=20`, `GENERATION_MIN_P=0.0`, `GENERATION_PRESENCE_PENALTY=1.5`, and `GENERATION_REPETITION_PENALTY=1.0`.

CO uses the same dataset-specific prompt and follows the LLM candidate-pool flow. By default, CO uses deterministic beam search with `BEAM_SIZE=8` as the candidate count (`num_return_sequences=8`); the returned candidates are decoded, sentence-split, deduplicated, and then passed to ILP/DPP/MMR.

CO output length is controlled by the selector budget: `BUDGET_SENTENCES=4`, so the final selected summary is capped at 4 sentences.

No extra hallucination-control instruction is added to the Qwen prompt.

`min_p=0.0` is a no-op in the local Transformers path. `presence_penalty=1.5` is applied with a generated-token logits processor so the local path matches the official API-style setting.
