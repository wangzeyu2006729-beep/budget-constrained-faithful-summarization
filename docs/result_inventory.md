# Result Inventory Corrections

Date: May 14, 2026

Dataset assignment is taken from each result file's `Dataset:` header and
checked against sample counts: CNN/DailyMail full test has 11,490 examples, and
Multi-News full test has 5,622 examples.

## Corrected Items

| Item | Correction |
| --- | --- |
| Multi-News BART baseline | The release now uses `beam4_baseline_hfrouge_shuffle_seed42_results_v2.txt` content as the canonical copied result. This restores MiniCheck = 94.41 instead of the earlier unavailable value. |
| CNN/DM BART selector rows | The only full-test local evidence found for BART+MMR/ILP/DPP is `scripts/_archive_bart_no_score_normalization_20260501/beam5_8_10_weights_annotated.csv`. It is copied under `results/raw/cnn_dailymail/bart/archive_bart_no_score_normalization_20260501/`; only its beam-5 rows are parsed into `paper_metrics.csv` because those are the Budget paper table values. |
| CNN/DM vs Multi-News BART | The Multi-News BART baseline is kept as a Multi-News result. It must not be used to fill the CNN/DM BART baseline row in the paper. |

## Still Missing Or Limited

| Paper/result need | Current status |
| --- | --- |
| CNN/DM BART baseline full result text backing the Budget paper row | Not found as a completed full-test `*_results.txt` in the source tree. A one-sample archived result exists, but it is not valid evidence for the paper table. |
| CNN/DM BART+MMR/ILP/DPP full result text files | Not found. Only the archived summary CSV is available, and it lacks BERTScore and FactKB. |
| Multi-News Llama-3-8B full baseline | Still running in `outputs/multi_news/llama3_8b/baseline/full_multi_news_baseline_requested_full_resume_llama_multinews_baseline` on May 14, 2026. It has progress and stage-output files, but no final `*_results.txt`. One-sample legacy result files exist and are not used as full-test evidence. |
| FactGraph | Requested by code, but unavailable in copied result files because the FactGraph repository is not configured. |
| External baselines in the Budget paper table | FactEdit, SimCLS, BRIO, EFactSum, and SummaReranker are paper comparison rows, not locally reproduced rows in this release. |

## Release Metrics Policy

`results/paper_metrics.csv` is regenerated from copied compact artifacts only.
Rows with `source_type=result_txt` come from completed result text files. Rows
with `source_type=archived_summary_csv` are included only to preserve the
available CNN/DM BART selector evidence and should be treated as lower-quality
evidence than full result text files. The `budget_table_status` column states
whether a row matches the Budget paper table, is an extra result, fills a blank
paper-table cell, or is only partial archive evidence.
