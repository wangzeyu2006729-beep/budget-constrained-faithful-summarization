# Result Inventory

Date: May 15, 2026

This release follows the result table as currently written in `paper/zeyu.tex`.
The table has filled local CNN/DailyMail rows and blank Multi-News rows.

## Main Paper Evidence

`results/paper_metrics.csv` is regenerated only from `results/raw/`. It contains
these local rows:

| Dataset | Method family | Evidence |
| --- | --- | --- |
| CNN/DM | BART baseline | `results/raw/cnn_dailymail/bart/baseline/.../beam4_baseline_raw_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | Qwen3.5-9B baseline | `results/raw/cnn_dailymail/qwen3_5_9b/baseline/.../baseline_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | Llama-3-8B baseline | `results/raw/cnn_dailymail/llama3_8b/baseline/.../baseline_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | Gemma-4-E4B-it baseline | `results/raw/cnn_dailymail/gemma4_e4b/baseline/.../baseline_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | BART+MMR | `results/raw/cnn_dailymail/bart/mmr/.../beam5_mmr_tri_metric_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | BART+ILP | `results/raw/cnn_dailymail/bart/ilp/.../beam5_ilp_tri_metric_hfrouge_shuffle_seed42_results.txt` |
| CNN/DM | BART+DPP | `results/raw/cnn_dailymail/bart/dpp/.../beam5_dpp_minicheck_redundancy_hfrouge_shuffle_seed42_results.txt` |

The metric values in those files match the filled local rows in `zeyu.tex`.

## External Reference Rows

FactEdit, SimCLS, BRIO-Mul, BRIO-Ctr, EFactSum, and SummaReranker are kept in
`results/external_reference_metrics.csv`. They are comparison rows from the
paper table, not locally reproduced rows in this release.

## Auxiliary Evidence

The following artifacts are retained but excluded from `paper_metrics.csv`:

- Multi-News baseline and PRIMERA CO results.
- CNN/DM Llama CO result variants.
- The older BART selector archive CSV.
- The corrected Multi-News BART baseline kept under `results/auxiliary/non_paper/`.

These files are useful for audit history but must not be treated as paper table
values until `zeyu.tex` is updated and the intended run is selected.

## Missing Or Pending

See `results/missing_results.csv`. The active server run is a Llama Multi-News
ILP CO run, so no final Llama Multi-News CO value should be reported yet.
