# gemma-4-E4B experiment entrypoints

This folder is the gemma-4-E4B entrypoint and implementation folder. It carries its own copy of the shared candidate-pool, CO, ordering, trace, and evaluation modules (`core/`, `metrics/`, `opt_selectors/`, `output/`, etc.), following the per-model isolation pattern.

Outputs are stored under `1_gemma_4_e4b/results/`.

## Model card

- **HF ID**: `google/gemma-4-E4B`
- **Architecture**: `AutoModelForCausalLM` (decoder-only)
- **dtype**: bf16
- **Official generation_config.json**: `temperature=1.0, top_k=64, top_p=0.95, do_sample=true`

## Memory notes

CO beam search with 8 beams will increase KV cache memory. If OOM occurs, fallback options:
1. Reduce `--generation-batch-size 1` (already default)
2. Add `low_cpu_mem_usage=True` to model loading
3. Last resort: switch to 4-bit quantization (bitsandbytes)

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

Multi-News uses `multi_news_concise_summary_only_v1` and changes the article label to `Articles:` with one extra instruction to synthesize shared facts across the documents without repetition.

## Decoding strategy

- **Baseline**: Sampling with official params (`temperature=1.0, top_p=0.95, top_k=64`)
- **CO**: `do_sample=False, num_beams=8, num_return_sequences=8, early_stopping=True`

## Dataset support

Supports `--dataset cnn_dailymail` (default) and `--dataset multi_news`.

## Quick start

```bash
# Baseline smoke test
python run.py --method baseline \
  --dataset cnn_dailymail --split test \
  --num-samples 1 --sample-mode head

# CO smoke test (ILP + tri-metric)
python run.py --method ilp \
  --dataset cnn_dailymail --split test \
  --num-samples 1 --sample-mode head \
  --tri-metric --w-rouge 0.01 --w-minicheck 0.495 --w-redundancy 0.495
```
