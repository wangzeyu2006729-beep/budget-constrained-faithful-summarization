# Validation Log

Latest validation date: May 15, 2026

## Completed In Current Paper-Table Alignment Pass

- Copied `<SOURCE_EXPERIMENT_ROOT>/zeyu.tex` to `paper/zeyu.tex`.
- Regenerated `results/paper_metrics.csv` from 14 local result text files that
  match filled rows in the current paper table.
- Moved reported CNN/DM Llama CO and PRIMERA Multi-News artifacts into
  `results/raw/`.
- Split external comparison rows into `results/external_reference_metrics.csv`.

Relevant current log:

- `logs/collect_paper_metrics_zeyu_20260515_103015.log`
- `logs/collect_paper_metrics_zeyu_final_20260515_103503.log`
- `logs/collect_paper_metrics_current_paper_20260515_105801.log`
- `logs/validate_release_static_zeyu_20260515_103329.log`
- `logs/validate_release_static_current_paper_20260515_110119.log`

## Static Checks

The current static validation passed with:

```bash
PYTHON=/path/to/python \
  scripts/run_live.sh --name validate_release_static_zeyu -- \
  bash scripts/validate_release_static.sh
```

The validation script performs shell syntax checks, Python AST parsing without
bytecode writes, and `--help` import checks for each model runner.

## Historical Checks

Earlier release setup also ran dry-run wrappers and static validation while
assembling the initial ACL release. Those logs remain under `logs/` for audit
history.

## Deferred

No smoke experiment or full experiment was started for this paper-table
alignment pass.
The current server already has a full Llama Multi-News ILP CO job running.
