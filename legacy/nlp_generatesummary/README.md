# Legacy NLP/NLM GenerateSummary Artifacts

This directory collects small, auditable artifacts from the older
`NLP_generatesummary` / `NLM_generatesummary` workspace so the release can trace
historical BART scripts and result files without committing the full 8.4 GB
working tree.

Included:

- `scripts/`: historical shell/Python launch, report, and analysis scripts.
- `bart/`: top-level BART runner scripts and small helper entrypoints.
- `bart/results/`: compact result tables and selected `*_results.txt` files.
- `docs/evaluation_metrics_guide.md`: historical metric notes.
- `*_inventory.csv`: generated file, script, and result inventories.

Excluded:

- `.venv/`, model weights, Hugging Face caches, dataset caches, and large
  intermediate progress traces.
- Vendored third-party packages such as `DPPy-master`, `bert_score-master`,
  `apricot-master`, `rebel-main`, and `FactScoreLite-main`.
- Archived weight-search subtrees whose contents are already summarized by the
  included compact CSV/Markdown reports.

Machine-specific roots were redacted in copied text artifacts:

- `/path/to/NLP_generatesummary` replaces the old local project root.
- `/path/to/NLM_data` replaces the old local data/cache root.

These files are retained for audit and provenance. The primary reproducibility
entrypoints for the paper remain the curated code under `src/` and the commands
in the top-level `README.md` and `docs/repro_runbook.md`.
