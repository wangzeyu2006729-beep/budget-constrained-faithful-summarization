# Budget-Constrained Faithful Summarization

This repository is the ACL-style reproducibility release for the paper snapshot:

```text
paper/zeyu.tex
```

The release was assembled from the original experiment workspace, referred to
here as `<SOURCE_EXPERIMENT_ROOT>`, plus compact legacy BART/NLM artifacts from
`<LEGACY_NLP_GENERATESUMMARY_ROOT>`. The original workspaces were not moved or
rewritten.

## What This Code Does

The implemented pipeline decouples generation from sentence-level selection:

1. A pretrained summarizer or instruction-tuned LLM generates candidate
   summaries.
2. Candidate summaries are split into sentences, exact duplicates are removed,
   and sentence provenance is retained.
3. Sentence utility is computed from ROUGE coverage and MiniCheck factuality.
4. Pairwise redundancy is computed with ROUGE-L F1.
5. ILP, MMR, or DPP-inspired greedy selection chooses a budgeted sentence set.
6. Selected sentences are ordered by source similarity and evaluated.

The DPP selector is a deterministic DPP-inspired greedy MAP heuristic over a
quality-weighted similarity kernel. The release should not be cited as exact
DPP sampling or as a proved submodular optimizer.

## Repository Layout

- `src/`: runnable model-specific code for BART, PRIMERA, Llama, Qwen, and Gemma.
- `scripts/`: release wrappers, live logging, validation, and metric extraction.
- `scripts/paper_runs/`: sanitized wrappers for the current paper table rows.
- `results/raw/`: compact result evidence for the local rows filled in the
  current paper table.
- `results/auxiliary/`: completed or partial artifacts that are useful for audit
  but not reported in the current `zeyu.tex` main table.
- `results/paper_metrics.csv`: regenerated metrics for the 14 local
  paper-reported rows.
- `results/external_reference_metrics.csv`: external comparison rows copied from
  `zeyu.tex`; these are not locally reproduced in this release.
- `results/missing_results.csv`: blank, pending, or unsupported paper/result
  items.
- `docs/`: code-paper audit, dependency notes, runbook, validation log, and
  result inventory.
- `paper/`: authoritative paper source and paper audit notes.
- `legacy/nlp_generatesummary/`: compact legacy BART/NLM scripts and inventories
  kept for provenance.

Full `outputs/`, model weights, dataset caches, progress traces, vendored
third-party repositories, and large archives are intentionally excluded.

## Install

```bash
cd /path/to/budget-constrained-faithful-summarization
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Optional metric assets are resolved through `NLM_ASSETS_DIR` or an untracked
`src/.nlm_assets.json`. See `docs/dependency_notes.md`.

## Validate And Regenerate Tables

All documented commands stream logs in real time and save a copy under `logs/`.

```bash
cd /path/to/budget-constrained-faithful-summarization

PYTHON=python3 \
  scripts/run_live.sh --name validate_release -- \
  bash scripts/validate_release_static.sh

scripts/run_live.sh --name collect_paper_metrics -- \
  python3 scripts/collect_paper_metrics.py
```

## Paper-Reported Local Reproduction Commands

Use `--num-samples 0` for the full test split. These commands match the local
result rows that are filled in the current paper table.

To launch the whole current-paper local run list through real-time logs:

```bash
PYTHON=python3 \
  bash scripts/paper_runs/run_current_paper_rows.sh
```

BART CNN/DailyMail direct baseline:

```bash
PYTHON=python3 \
  scripts/run_live.sh --name full_bart_cnn_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model bart \
    --method baseline \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 4 \
    --output-tag full_bart_cnn_baseline
```

BART CNN/DailyMail CO selectors:

```bash
for method in mmr ilp dpp; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_bart_cnn_${method}" -- \
    bash scripts/run_release_experiment.sh \
      --model bart \
      --method "$method" \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --beam-size 5 \
      --output-tag "full_bart_cnn_${method}"
done
```

Instruction-tuned CNN/DailyMail direct baselines:

```bash
for model in qwen3_5_9b llama3_8b gemma4_e4b; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_${model}_cnn_baseline" -- \
    bash scripts/run_release_experiment.sh \
      --model "$model" \
      --method baseline \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --output-tag "full_${model}_cnn_baseline"
done
```

Llama CNN/DailyMail CO rows reported as `new w.` and `old w.`:

```bash
# MMR/ILP new weights: rouge=0.20, minicheck=0.60, redundancy=0.20
for method in mmr ilp; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_llama_cnn_${method}_new_w" -- \
    bash scripts/run_release_experiment.sh \
      --model llama3_8b \
      --method "$method" \
      --dataset cnn_dailymail \
      --num-samples 0 \
      --beam-size 8 \
      --budget-sentences 4 \
      --output-tag "full_llama_cnn_${method}_new_w" -- \
      --w-rouge 0.20 \
      --w-minicheck 0.60 \
      --w-redundancy 0.20
done

# DPP old weights: rouge=0.01, minicheck=0.495, redundancy=0.495
PYTHON=python3 \
  scripts/run_live.sh --name full_llama_cnn_dpp_old_w -- \
  bash scripts/run_release_experiment.sh \
    --model llama3_8b \
    --method dpp \
    --dataset cnn_dailymail \
    --num-samples 0 \
    --beam-size 8 \
    --budget-sentences 4 \
    --output-tag full_llama_cnn_dpp_old_w -- \
    --w-rouge 0.01 \
    --w-minicheck 0.495 \
    --w-redundancy 0.495
```

PRIMERA Multi-News rows:

```bash
PYTHON=python3 \
  scripts/run_live.sh --name full_primera_multinews_baseline -- \
  bash scripts/run_release_experiment.sh \
    --model primera_multinews \
    --method baseline \
    --dataset multi_news \
    --num-samples 0 \
    --beam-size 5 \
    --output-tag full_primera_multinews_baseline

for method in mmr ilp dpp; do
  PYTHON=python3 \
    scripts/run_live.sh --name "full_primera_multinews_${method}" -- \
    bash scripts/run_release_experiment.sh \
      --model primera_multinews \
      --method "$method" \
      --dataset multi_news \
      --num-samples 0 \
      --beam-size 8 \
      --budget-sentences 8 \
      --output-tag "full_primera_multinews_${method}"
done
```

## Output Files

Each run writes under `results/runs/<dataset>/<model>/<method>/<output-tag>/`.
The compact paper evidence copied into this release is under `results/raw/`.
Auxiliary result files are retained under `results/auxiliary/` but are not
parsed into `results/paper_metrics.csv`.

## Paper-Code Consistency Notes

- `paper/zeyu.tex` is the release paper source and its table has been updated to
  include the local rows present in the current paper text.
- `results/paper_metrics.csv` contains the 14 local rows with filled values:
  CNN/DM BART, Qwen, Llama, Gemma baselines; CNN/DM BART+MMR/ILP/DPP; CNN/DM
  Llama+MMR/ILP/DPP; and Multi-News PRIMERA baseline/MMR/ILP/DPP.
- Multi-News Qwen/Llama/Gemma rows and Multi-News Llama CO rows remain blank or
  pending in the current paper and are kept as auxiliary evidence only when
  local artifacts exist.
- FactGraph appears as unavailable in result files and should not be claimed as
  reported.
- The current paper source still contains placeholder ACL template material and
  missing assets; see `paper/AUDIT_NOTES.md`.

## GitHub

Repository:

```text
https://github.com/wangzeyu2006729-beep/budget-constrained-faithful-summarization
```

The release is maintained on `main` per the project request.
