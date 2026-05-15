# ACL Code-Paper Audit

Authoritative paper source for this release: `paper/zeyu.tex`.

ACL/ARR references used for this release:

- https://acl-org.github.io/ACLPUB/formatting.html
- https://aclrollingreview.org/responsibleNLPresearch/
- https://aclrollingreview.org/authorchecklist

## Project Map

- Paper: `paper/zeyu.tex`, copied from `<SOURCE_EXPERIMENT_ROOT>/zeyu.tex`.
- Core code: `src/bart`, `src/primera_multinews`, `src/llama3_8b`,
  `src/qwen3_5_9b`, and `src/gemma4_e4b`.
- Main entrypoints: each model directory has `run.py`; release-level execution
  goes through `scripts/run_release_experiment.sh`.
- CLI chain: `scripts/run_live.sh` streams logs, then
  `scripts/run_release_experiment.sh` resolves model/method/default paths, then
  `src/<model>/run.py` calls the model-specific orchestration, data loading,
  generation, selection, evaluation, and result saving modules.
- Results: local rows reported in `zeyu.tex` are in `results/raw/`; non-reported
  evidence is in `results/auxiliary/`.

## Claim-To-Code Map

| Paper claim or requirement | Release implementation evidence | Status |
| --- | --- | --- |
| Candidate generation creates multiple summaries before selection. | `src/*/core/orchestration.py` calls model generation and records beam/candidate payloads. | Matches for CO runs. Direct baselines generate one final output. |
| Candidate summaries are split into sentences and exact duplicates are removed. | `build_candidate_pool_trace` in `src/*/core/orchestration.py` builds `unique_sentences` and provenance. | Matches. |
| Sentence provenance is retained. | Candidate pool sources store beam index, sentence position, and score fields in stage outputs/result logs. | Matches. |
| Coverage utility uses ROUGE-1 recall plus ROUGE-2 recall. | `compute_rouge_utility_scores` in `src/*/core/features.py`. | Matches. |
| Factuality utility uses MiniCheck sentence consistency probability. | `compute_minicheck_utility_scores` in `src/*/core/features.py`. | Matches. MiniCheck is also an evaluation diagnostic, so the paper should treat it as optimization-aligned. |
| Utility combines coverage and MiniCheck after per-pool min-max normalization. | `_per_sample_min_max` and `compute_tri_metric_utility_scores` in `src/*/core/features.py`. | Matches current implementation. Do not describe this as global or robust percentile normalization for these rows. |
| Redundancy uses pairwise ROUGE-L F1. | `compute_redundancy_matrix` in `src/*/core/features.py`. | Matches. |
| ILP uses a soft pairwise redundancy penalty. | `_solve_soft_ilp` in `src/*/opt_selectors/sentence_level/ilp.py` maximizes utility minus pairwise penalty with `1 <= sum x <= budget`. | Matches. Note the older hard ILP path remains for non-tri-metric modes. |
| MMR greedily balances utility and maximum redundancy. | `mmr_select` in `src/*/opt_selectors/sentence_level/mmr.py`. | Matches. |
| DPP is DPP-inspired, not exact DPP sampling. | `dpp_select` in `src/*/opt_selectors/sentence_level/dpp.py` uses a quality-weighted similarity kernel with deterministic greedy log-det selection. | Matches the cautious wording in `zeyu.tex`. |
| Selected sentences are ordered by source similarity. | `order_selected_sentences` in `src/*/core/orchestration.py`. | Matches. |
| CNN/DailyMail and Multi-News are target datasets. | Data loaders support both where applicable. | Code supports them, but `zeyu.tex` currently reports filled local numbers only for CNN/DM rows. |
| Budgets are sentence-count budgets in current experiments. | Result headers show direct full output for baselines and 4-sentence budgets for CNN/DM BART CO rows. | Matches. Token/word budgets are not implemented in reported runs. |
| Evaluation reports ROUGE, BERTScore, FactCC, MiniCheck, AlignScore, FactKB. | `src/*/metrics/evaluation.py` and copied `results/raw/**/*_results.txt`. | Matches for the seven local reported rows. FactGraph is unavailable and is not a reported table metric. |
| Prior systems are external reference baselines when not re-evaluated locally. | `results/external_reference_metrics.csv` stores the `zeyu.tex` external rows separately. | Matches. They are not in `paper_metrics.csv`. |
| Llama CO and Multi-News rows are blank in `zeyu.tex`. | Related artifacts are kept under `results/auxiliary/not_reported_in_zeyu/`. | Matches release policy; do not merge these into paper metrics unless the paper is updated. |

## Inconsistency And Risk Notes

| Item | Paper/source claim | Code/result evidence | Risk | Recommendation |
| --- | --- | --- | --- | --- |
| Placeholder abstract | `zeyu.tex` abstract is ACL template text. | `paper/zeyu.tex` copied verbatim. | High paper-quality risk. | Fix paper text before submission; release keeps the source visible. |
| Template tail | `zeyu.tex` contains ACL template instructions after the first Conclusion. | Present in `paper/zeyu.tex`. | High paper-quality risk. | Remove from the paper before submission. |
| Missing assets | `latex/Pipeline.png` and `custom.bib` are referenced. | Those files are not included in the release. | High compile/submission risk. | Add assets or revise paper source. |
| Multi-News values | Table cells are blank. | Completed auxiliary results exist for several rows. | Medium reporting risk. | Keep blank unless the paper is intentionally updated and audited. |
| CNN/DM Llama CO values | Table cells are blank. | Related result files exist but are auxiliary. | Medium reporting risk. | Do not report from auxiliary without updating paper and selecting the intended weight/run. |
| FactGraph | Code can request it, but result files mark it unavailable. | No completed FactGraph metric evidence. | Medium metric risk. | Do not claim FactGraph in paper results. |
| Theoretical guarantees | Method uses heuristics and pairwise penalties. | Code uses ILP/MMR/DPP-inspired selectors. | Medium wording risk. | Avoid strict submodularity/DPP sampling claims. |

## Release Adjustments

- `paper/zeyu.tex` replaces the earlier Budget draft as the authoritative paper
  file.
- `results/paper_metrics.csv` is regenerated from only seven locally reported
  rows in `zeyu.tex`.
- External reference baselines are split into
  `results/external_reference_metrics.csv`.
- Multi-News rows, CNN/DM Llama CO rows, and older BART archive CSV evidence
  remain in `results/auxiliary/not_reported_in_zeyu/`.
- No core experiment logic was changed for this zeyu alignment pass.
