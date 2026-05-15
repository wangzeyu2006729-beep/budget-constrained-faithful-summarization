# Validation Log

Date: May 14, 2026

## Completed

- Generated `results/paper_metrics.csv` from 16 copied result text files and
  one archived BART selector summary CSV.
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
- `logs/collect_paper_metrics_result_inventory_20260514_*.log`
- `logs/validate_release_result_inventory_20260514_*.log`
- `logs/collect_paper_metrics_paper_table_fix_20260514_*.log`
- `logs/validate_release_paper_table_fix_20260514_*.log`
- `logs/collect_paper_metrics_aux_move_20260514_*.log`
- `logs/validate_release_aux_move_20260514_*.log`
- `logs/collect_paper_metrics_llama_mn_baseline_20260514_232910.log`
- `logs/validate_release_static_after_llama_mn_baseline_20260514_233210.log` records a failed validation with system `python3` because `pysbd` was not installed.
- `logs/validate_release_static_after_llama_mn_baseline_venv_20260514_233218.log` records a failed validation after removing the machine-specific asset config; AlignScore was resolved too early at import time.
- `logs/validate_release_static_after_lazy_assets_20260514_233326.log` records the next failed validation; MiniCheck was resolved too early at import time.
- `logs/validate_release_static_after_lazy_minicheck_20260514_233415.log` records the passing static validation after AlignScore and MiniCheck asset checks were made lazy.
- `logs/collect_paper_metrics_lf_20260514_233544.log` records regeneration after normalizing CSV line endings.
- `logs/validate_release_static_final_20260514_233550.log` records the final passing static validation.

## Deferred

The planned actual `NUM_SAMPLES=2` model smoke runs were not started during
release creation because the original experiment directory had an active
full-test GPU job. The earlier Llama Multi-News full baseline later completed
and was copied into `results/raw/`; the current pending job is Llama Multi-News
CO selection:

```text
tmux session llama_mn_ilp_b6, Llama Multi-News ILP, generation batch size 6
```

Starting additional model and metric evaluation jobs during that run could
interfere with the active experiment. The exact smoke commands remain in
`README.md` and `docs/repro_runbook.md`.
