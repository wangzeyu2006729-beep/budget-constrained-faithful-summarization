# ACL Code-Paper Audit

Authoritative paper source: `paper/Budget-constrained and faithful.tex`.

ACL/ARR references used for this release:

- https://acl-org.github.io/ACLPUB/formatting.html
- https://aclrollingreview.org/responsibleNLPresearch/
- https://aclrollingreview.org/authorchecklist

## Claim-To-Code Map

| Paper claim or requirement | Release implementation evidence | Status |
| --- | --- | --- |
| Candidate generation creates multiple summaries before selection. | `src/*/core/orchestration.py` calls model generation and records `beam_candidates`; LLM backends use `SummaryGenerator.generate_batch`. | Matches. |
| Candidate summaries are split into sentences and exact duplicates are removed. | `build_candidate_pool_trace` in `src/*/core/orchestration.py` builds `unique_sentences` with exact-string deduplication and provenance. | Matches. |
| Coverage utility uses ROUGE-1 recall plus ROUGE-2 recall. | `compute_rouge_utility_scores` in `src/*/core/features.py`. | Matches. |
| Factuality utility uses MiniCheck sentence consistency probability. | `compute_minicheck_utility_scores` in `src/*/core/features.py`. | Matches. |
| Tri-metric utility combines coverage and MiniCheck after per-sample normalization. | `_per_sample_min_max` and `compute_tri_metric_utility_scores` in `src/*/core/features.py`. | Mostly matches, but the paper should not claim robust/global calibration for these copied runs. |
| Redundancy uses pairwise ROUGE-L F1. | `compute_redundancy_matrix` in `src/*/core/features.py`. | Matches. |
| ILP uses a soft pairwise redundancy penalty in tri-metric mode. | `_solve_soft_ilp` in `src/*/opt_selectors/sentence_level/ilp.py` maximizes utility minus pairwise penalty with `1 <= sum x <= budget`. | Matches. |
| MMR greedily balances utility and maximum redundancy to selected sentences. | `mmr_select` in `src/*/opt_selectors/sentence_level/mmr.py`. | Matches. |
| DPP is DPP-inspired, not a full probabilistic DPP sampler. | `dpp_select` in `src/*/opt_selectors/sentence_level/dpp.py` builds a quality-weighted similarity kernel and uses deterministic greedy log-det MAP. | The paper should avoid claiming exact DPP sampling. |
| Selected sentences are ordered by source similarity. | `order_selected_sentences` in `src/*/core/orchestration.py` maps selected sentences to source sentences with ROUGE-L F1 and sorts by source index. | Matches. |
| CNN/DailyMail and Multi-News test splits are used. | `src/bart/core/data.py`, `src/primera_multinews/core/data.py`, and LLM data loaders use Hugging Face datasets. Copied result files use `Split: test`. | Matches. |
| Budgets are dataset-specific sentence budgets. | BART and LLM CNN/DM use 4 sentences; PRIMERA Multi-News CO uses 8 sentences in copied result headers. | Matches. |
| Candidate count is larger for CO than direct baselines. | CO result headers show `Candidate count: 8` or `Beam size: 8`; PRIMERA baseline uses beam 5; BART baseline uses beam 4. | Matches. |
| Evaluation reports ROUGE, BERTScore, FactCC, MiniCheck, AlignScore, FactKB. | `src/*/metrics/evaluation.py` and copied `results/raw/**/*_results.txt`. | Mostly matches. MiniCheck is unavailable in several copied Multi-News baseline result files; FactGraph is unavailable. |
| Objective is a monotone submodular function with facility-location-style diversity. | Budget draft line 93 claims this, but release code implements weighted modular utility plus selector-specific pairwise redundancy/DPP-inspired log-det behavior. | Does not match; revise paper wording before submission. |
| Commands produce real-time logs. | `scripts/run_live.sh` wraps commands with `stdbuf` and `tee`. README and runbook use it for documented commands. | Matches project instruction. |

## Known Paper-Side Issues To Fix Before Submission

- `paper/Budget-constrained and faithful.tex` contains placeholder abstract text from the ACL template.
- `paper/Budget-constrained and faithful.tex` currently claims a monotone submodular objective; the copied implementation does not establish that objective class.
- `paper/Budget-constrained and faithful.tex` contains ACL template material after the main paper draft; this should be removed before submission.
- `paper/Budget-constrained and faithful.tex` references `latex/Pipeline.png`, but that asset is not present in the release.
- `paper/Budget-constrained and faithful.tex` references `custom.bib`, but no bibliography file is present in the source experiment directory or release.
- `paper/Budget-constrained and faithful.tex` contains author names and affiliations in the source. If this package is submitted for anonymous review, the paper source and supplementary files must be anonymized.
- Several result table cells in `paper/Budget-constrained and faithful.tex` are blank even though matching result files exist in `results/raw/`.
- Original README/code comments sometimes say LLM CO uses "sampled candidates"; in the current LLM implementation, `GENERATION_DO_SAMPLE=auto` means baselines sample while CO candidate generation uses beam-style generation unless `--do-sample true` is explicitly passed. Paper wording should say "candidate count" or "beam candidates" for the copied CO runs.
- The paper should not claim FactGraph as a completed reported metric unless a final FactGraph evaluation is added.
- The active Llama Multi-News baseline was not copied because, on May 14, 2026, it still had only progress files and no final result file.

## Code-Side Release Adjustments

- The original source tree vendored `DPPy-master`; this release excludes it as third-party bulk material.
- The DPP selector had an unused `dppy.finite_dpps.FiniteDPP` import. The release copy removes that unused import so the DPP selector runs without vendored DPPy while preserving the implemented greedy log-det behavior.
- The original source tree vendored `bert_score-master`; this release prefers the installed `bert_score` package and only falls back to an external asset if needed.
- Source directories no longer contain historical `results/` subfolders. Compact result text files live only under `results/raw/`.
- Copied result files replace the original absolute experiment root with `<SOURCE_EXPERIMENT_ROOT>` to avoid leaking local filesystem paths in the release metrics artifacts.
