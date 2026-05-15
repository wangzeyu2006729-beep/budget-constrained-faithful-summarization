# Method Inventory

Primary FACT metric candidate: **MiniCheck**

| method_name | method_type | paper/source | status | current_samples | entrypoint_or_dir | missing_prerequisites | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline3 | bart_baseline | Local project baseline | runnable | 500 | /path/to/NLP_generatesummary/bart/run.py |  | Baseline3 (Top-1 Beam -> First 4 Sentences) |
| baseline_raw |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| brio_ctr | paper_reproduction | ACL 2022 Long Papers | runnable | None | /path/to/NLP_generatesummary/papers/复现baseline/brio_ctr_reproduction/run_unified.sh |  |  |
| consum_fenice_0_75 | paper_reproduction | ConSUM reranking paper | partial | None | /path/to/NLP_generatesummary/papers/复现baseline/consum_cnndm_second_stage_reranker/scripts/rerank_and_evaluate.py | data_cache[test]: missing; pseudo_reference_files[test]: missing; score_files[test]: missing; candidate_files[test]: missing | The package also exposes baseline, FENICE-0.0, and MBR-1.0 companion systems. |
| dpp_minicheck_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| dpp_minicheck_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| dpp_rouge_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| dpp_rouge_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| factedit | paper_reproduction | EMNLP 2022 | runnable | None | /path/to/NLP_generatesummary/scripts/run_factedit_unified.sh |  |  |
| ilp_minicheck_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| ilp_minicheck_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| ilp_rouge_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| ilp_rouge_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| lexisem | paper_reproduction | Information Sciences 2025 | partial | 4997 | /path/to/NLP_generatesummary/papers/复现baseline/lexisem_reproduction/eval_lexisem.py | candidate_dir: /path/to/NLP_generatesummary/LexiSem-main/results/result_cnndm/candidate; reference_dir: /path/to/NLP_generatesummary/LexiSem-main/results/result_cnndm/reference | Only smoke checkpoint exists in the workspace right now. |
| lns_minicheck_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| lns_minicheck_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| lns_rouge_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| lns_rouge_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| mbr_summary_mbr |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| mmr_minicheck_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| mmr_minicheck_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| mmr_rouge_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| mmr_rouge_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| pareto_summary_pareto |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| simcls | paper_reproduction | ACL 2021 Short Papers | runnable | None | /path/to/NLP_generatesummary/scripts/run_simcls_train.sh |  |  |
| submodular_acl2011 | paper_reproduction | Hui Lin, Jeff Bilmes, ACL 2011 | runnable | None | /path/to/NLP_generatesummary/papers/复现baseline/submodular_greedy/experiments/run_greedy.py |  |  |
| submodular_budgeted | paper_reproduction | Hui Lin, Jeff Bilmes, NAACL 2010 | runnable | None | /path/to/NLP_generatesummary/papers/复现baseline/submodular_greedy/experiments/run_greedy.py |  |  |
| submodular_minicheck_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| submodular_minicheck_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| submodular_rouge_only |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| submodular_rouge_redundancy |  |  | runnable | None | /path/to/NLP_generatesummary/bart/run.py |  |  |
| summa_reranker | paper_reproduction | ACL 2022 Long Papers | partial | None | /path/to/NLP_generatesummary/papers/复现baseline/summa_reranker_cnndm_second_stage_reranker/scripts/rerank_and_evaluate.py | official_data_root: missing; official_summaries_root: missing; official_scored_root: missing |  |
