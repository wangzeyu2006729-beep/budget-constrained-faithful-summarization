# Validation Log

Date: May 14, 2026

## Completed

- Generated `results/paper_metrics.csv` from 16 copied result files.
- Ran shell syntax checks on release shell scripts.
- Ran Python AST parsing on release Python files without bytecode writes.
- Ran `--help` import checks for:
  - `src/bart/run.py`
  - `src/primera_multinews/run.py`
  - `src/llama3_8b/run.py`
  - `src/qwen3_5_9b/run.py`
  - `src/gemma4_e4b/run.py`
- Ran `DRY_RUN=1` checks for:
  - BART CNN/DailyMail baseline wrapper
  - PRIMERA Multi-News MMR wrapper

Relevant logs:

- `logs/collect_paper_metrics_20260514_111446.log`
- `logs/collect_paper_metrics_redacted_20260514_111514.log`
- `logs/validate_release_20260514_111546.log` records the first validation failure, caused by the removed vendored BERTScore path.
- `logs/validate_release_retry_20260514_111634.log` records the passing validation after the release code was updated to prefer the installed `bert_score` package.
- `logs/dryrun_bart_baseline_20260514_111720.log`
- `logs/dryrun_primera_mmr_20260514_111720.log`

## Deferred

The planned actual `NUM_SAMPLES=2` model smoke runs were not started during
release creation because the original experiment directory still had an active
Llama Multi-News full baseline process using the GPU:

```text
PID 2474746, elapsed over 22 hours, about 42GB GPU memory in use
```

Starting additional model and metric evaluation jobs during that run could
interfere with the active experiment. The exact smoke commands remain in
`README.md` and `docs/repro_runbook.md`.
