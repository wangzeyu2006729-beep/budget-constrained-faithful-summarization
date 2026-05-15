# Result Inventory

Date: May 15, 2026

This release follows the local result rows in the current paper table pasted by
the author. `results/paper_metrics.csv` is regenerated only from
`results/raw/`.

## Main Paper Evidence

| Dataset | Method family | Evidence |
| --- | --- | --- |
| CNN/DM | BART baseline | `results/raw/cnn_dailymail/bart/baseline/.../beam4_baseline_raw_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | Qwen3.5-9B baseline | `results/raw/cnn_dailymail/qwen3_5_9b/baseline/.../baseline_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | Llama-3-8B baseline | `results/raw/cnn_dailymail/llama3_8b/baseline/.../baseline_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | Gemma-4-E4B-it baseline | `results/raw/cnn_dailymail/gemma4_e4b/baseline/.../baseline_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | BART+MMR/ILP/DPP | `results/raw/cnn_dailymail/bart/{mmr,ilp,dpp}/.../*_results.txt` |
| CNN/DM | Llama+MMR/ILP new weights | `results/raw/cnn_dailymail/llama3_8b/{mmr,ilp}/full_cnn_dailymail_co_tri_metric_balanced_wr020_wm060_wd020_reuse_ilp_stage1/*_results.txt` |
| CNN/DM | Llama+DPP old weights | `results/raw/cnn_dailymail/llama3_8b/dpp/full_cnn_dailymail_co_tri_metric_requested_full_resume_llama_cnn_co/*_results.txt` |
| Multi-News | PRIMERA baseline | `results/raw/multi_news/primera_multinews/baseline/.../beam5_baseline_hfrouge_shuffle_seed42_results.txt` |
| Multi-News | PRIMERA+MMR/ILP/DPP | `results/raw/multi_news/primera_multinews/{mmr,ilp,dpp}/.../*_results.txt` |

These 14 rows are parsed into `results/paper_metrics.csv`.

## External Reference Rows

FactEdit, SimCLS, BRIO-Mul, BRIO-Ctr, EFactSum, and SummaReranker are kept in
`results/external_reference_metrics.csv`. They are comparison rows from the
paper table, not locally reproduced rows in this release.

## Auxiliary Evidence

The following artifacts are retained but excluded from `paper_metrics.csv`:

- Multi-News Qwen/Gemma/Llama baseline artifacts whose cells are blank or
  unavailable in the current pasted table.
- CNN/DM Llama CO variants that do not correspond to the paper labels
  `(new w.)` or `(old w.)`.
- The older BART selector archive CSV.
- The corrected Multi-News BART baseline kept under `results/auxiliary/non_paper/`.

## Missing Or Pending

See `results/missing_results.csv`. The active server run is a Llama Multi-News
ILP CO run, so no final Llama Multi-News CO value should be reported yet.
