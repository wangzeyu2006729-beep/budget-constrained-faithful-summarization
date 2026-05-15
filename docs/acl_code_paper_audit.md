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
| Evaluation reports ROUGE, BERTScore, FactCC, MiniCheck, AlignScore, FactKB. | `src/*/metrics/evaluation.py`, copied `results/raw/**/*_results.txt`, and one archived BART selector summary CSV. | Mostly matches. Several LLM Multi-News baseline result files still lack MiniCheck; FactGraph is unavailable. The corrected Multi-News BART v2 result is kept only as non-paper auxiliary evidence. |
| Objective should be described as the implemented sentence-level utility plus selector-specific redundancy handling, not as a proven monotone submodular objective. | `paper/Budget-constrained and faithful.tex` now states that the release implementation uses modular utility/factuality scores and pairwise redundancy penalties or greedy diversity terms, without claiming a general submodularity guarantee. | Matches after release edit; do not reintroduce the stronger theoretical claim without new code/theory evidence. |
| Commands produce real-time logs. | `scripts/run_live.sh` wraps commands with `stdbuf` and `tee`. README and runbook use it for documented commands. | Matches project instruction. |

## Known Paper-Side Issues To Fix Before Submission

- `paper/Budget-constrained and faithful.tex` references `custom.bib`, but no bibliography file is present in the source experiment directory or release.
- `paper/Budget-constrained and faithful.tex` contains author names and affiliations in the source. If this package is submitted for anonymous review, the paper source and supplementary files must be anonymized.
- The release paper snapshot now fills locally available Multi-News Qwen3.5-9B, Llama-3-8B, and Gemma-4-E4B-it baseline rows and uses `--` for unavailable or unreproduced cells instead of silent blanks.
- The CNN/DM BART baseline row in the Budget paper has no completed full-test `*_results.txt` evidence found in the source tree.
- CNN/DM BART selector rows are supported only by an archived summary CSV in this release; full selector `*_results.txt` evidence was not found in the source tree.
- The Multi-News BART baseline is a real Multi-News result and must not be used to fill the CNN/DM BART baseline row.
- Remaining missing or limited result evidence is tracked in `results/missing_results.csv`.
- Original README/code comments sometimes say LLM CO uses "sampled candidates"; in the current LLM implementation, `GENERATION_DO_SAMPLE=auto` means baselines sample while CO candidate generation uses beam-style generation unless `--do-sample true` is explicitly passed. Paper wording should say "candidate count" or "beam candidates" for the copied CO runs.
- The paper should not claim FactGraph as a completed reported metric unless a final FactGraph evaluation is added.
- The Llama Multi-News baseline completed on May 14, 2026 and is now copied into `results/raw/`; its MiniCheck metric is unavailable in the copied result due a recorded `torch.cat()` empty-tensor failure.
- Llama Multi-News CO selector rows remain pending until final `*_results.txt` files exist.

## Code-Side Release Adjustments

- The original source tree vendored `DPPy-master`; this release excludes it as third-party bulk material.
- The DPP selector had an unused `dppy.finite_dpps.FiniteDPP` import. The release copy removes that unused import so the DPP selector runs without vendored DPPy while preserving the implemented greedy log-det behavior.
- The original source tree vendored `bert_score-master`; this release prefers the installed `bert_score` package and only falls back to an external asset if needed.
- Source directories no longer contain historical `results/` subfolders. Compact result artifacts live under `results/raw/`.
- Copied result files replace the original absolute experiment root with `<SOURCE_EXPERIMENT_ROOT>` to avoid leaking local filesystem paths in the release metrics artifacts.
- The committed release no longer includes a machine-specific `src/.nlm_assets.json`; users should set `NLM_ASSETS_DIR` or create their own local untracked config file.
- AlignScore and MiniCheck asset checks are lazy in the release copy so `run.py --help` works without local metric assets; actual metric computation still requires the documented assets.
- The release paper snapshot replaces the ACL-template abstract, removes trailing ACL template material, replaces the missing `latex/Pipeline.png` include with an inline text pipeline, and weakens the method wording to match the implemented selectors.
