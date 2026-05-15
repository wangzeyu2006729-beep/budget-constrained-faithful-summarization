# Llama-3.1-8B-Instruct Experiment Runner

This directory contains the release copy of the Meta-Llama-3.1-8B-Instruct
generate-then-optimize runner.

## Model And Prompt

- Hugging Face model: `meta-llama/Llama-3.1-8B-Instruct`
- Dataset prompts:
  - CNN/DailyMail: `llama3_cnn_dailymail_concise_summary_only_v1`
  - Multi-News: `llama3_multi_news_summary_only_v4`
- Input cap: `8192` tokens in the local experiment configuration.
- Max new tokens: `32768`; generation normally stops earlier on EOS.
- Decoding mode: `do_sample=auto`, which means direct baselines use the
  model-card sampling configuration, while CO runs with multiple candidates use
  deterministic beam-style generation unless `--do-sample true` is passed.

## Metrics

The runner requests ROUGE, BERTScore, FactCC, MiniCheck, AlignScore, FactGraph,
and FactKB. FactGraph requires an external repo path and is marked unavailable
in the copied result files when that repo is not configured.

## Release Usage

Prefer the top-level release wrapper so output paths stay inside the release
tree:

```bash
cd /path/to/NLP_acl_repro_release

scripts/run_live.sh --name llama_multinews_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method baseline \
    --dataset multi_news \
    --num-samples 0 \
    --output-tag full_llama_multinews_baseline
```

For gated Llama access, authenticate with Hugging Face before running:

```bash
# Set HF_TOKEN in your shell to a Hugging Face read token with Llama access.
export HF_TOKEN
```
