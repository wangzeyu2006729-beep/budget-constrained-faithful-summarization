# NLP ACL Reproducibility Release

This directory is a clean reproducibility package for the ILP, DPP, and MMR
summarization experiments. It was built from
`/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment` without moving or modifying the
original experiment directory.

Authoritative paper source: `paper/Budget-constrained and faithful.tex`.

## Layout

- `src/`: runnable model-specific experiment code.
- `scripts/`: release wrappers, live logging, validation, and metric extraction.
- `results/raw/`: copied compact `*_results.txt` files only.
- `results/paper_metrics.csv`: compact metrics regenerated from `results/raw/`.
- `docs/`: ACL/code-paper audit, dependency notes, and reproduction runbook.
- `paper/`: raw authoritative paper snapshot, older draft snapshot, and paper-side audit notes.

Heavy artifacts are intentionally excluded: full `outputs/`, stage traces,
progress checkpoints, training/evaluation run logs, caches, vendored
third-party repositories, and archived large-model folders. The small `logs/`
directory in this release only records release validation and dry-run commands.

## Quick Checks

Run all documented commands through `scripts/run_live.sh` so logs print in real
time and are also saved under `logs/`.

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name validate_release -- \
  bash scripts/validate_release_static.sh
```

Dry-run a release wrapper without loading a model:

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

DRY_RUN=1 PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name dryrun_primera_mmr -- \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method mmr \
    --dataset multi_news \
    --num-samples 2 \
    --beam-size 8 \
    --budget-sentences 8 \
    --output-tag dryrun_primera_mmr
```

Regenerate the compact metrics table:

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

scripts/run_live.sh --name collect_paper_metrics -- \
  python3 scripts/collect_paper_metrics.py
```

## Small Reproduction

These smoke commands run tiny experiments and stream logs live:

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name smoke_bart_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 2 \
    --beam-size 4 \
    --output-tag smoke_bart_baseline

PYTHON=/home/zeyu/projects/NLP_ilp_dpp_mmr_experiment/.venv/bin/python \
  scripts/run_live.sh --name smoke_primera_mmr -- \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method mmr \
    --dataset multi_news \
    --num-samples 2 \
    --beam-size 8 \
    --budget-sentences 8 \
    --output-tag smoke_primera_mmr
```

Full commands and caveats are in `docs/repro_runbook.md`.
Validation performed during release creation is recorded in
`docs/validation_log.md`.

## ACL Notes

The release follows the ACL supplemental-material principle that software and
data artifacts should be documented and supplemental, while the paper should
remain self-contained. The current paper snapshot still has paper-side issues;
see `docs/acl_code_paper_audit.md` and `paper/AUDIT_NOTES.md` before submission.

## Publish To GitHub

The publication-style repository name derived from the paper topic is:

```text
budget-constrained-faithful-summarization
```

The GitHub repository is:

```text
https://github.com/wangzeyu2006729-beep/budget-constrained-faithful-summarization
```

This server currently has no `gh` CLI, so creating or renaming repositories
requires a token. The release directory is already initialized as a local git
repository on branch `main`.

```bash
cd /home/zeyu/projects/NLP_acl_repro_release

git config user.name "Your Name"
git config user.email "you@example.com"

GH_TOKEN=YOUR_GITHUB_TOKEN \
  scripts/run_live.sh --name publish_github -- \
  bash scripts/publish_to_github.sh
```

By default this creates a private GitHub repo. To publish publicly, pass
`VISIBILITY=public`, but do not do that for anonymous ACL review material.
