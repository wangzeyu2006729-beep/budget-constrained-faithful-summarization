# Tri-metric Weight Search Summary

## Goal

Find a shared tri-metric weight for the explicit-weight sentence-level methods under the current main setting:

- `beam = 5`
- `budget = 4`
- `split = validation`
- `num_samples = 50`
- full evaluation suite

The tri-metric weights are:

- `w_rouge`
- `w_minicheck`
- `w_redundancy`

## Method Scope

The search process was narrowed in stages.

### Stage 1: Initial coarse sweep on MMR only

MMR was used first as a cheap explicit-weight anchor. The initial coarse grid showed a stable trend:

- increasing `w_rouge` did not reliably improve final summary-level ROUGE
- the useful tradeoff was mainly between `MiniCheck` and `Redundancy`
- the best local point in that first sweep was around `0.0 / 0.5 / 0.5`

This stage served as direction finding rather than the final decision.

### Stage 2: Restrict the final shared-weight search to explicit-weight methods

For the final shared-weight decision, only the explicit-weight methods were treated as primary:

- `MMR`
- `LNS`

The following methods were not used to decide the final shared weight:

- `baseline_raw`: no optimization weights
- `ILP`: threshold-based constraint, not the same explicit-weight form
- `DPP`, `Submodular`: matrix-scaling form, not the same explicit-weight form
- `MBR`: separate 2D weight form
- `Pareto`: original method is not a linear weighted objective

## Results Used for Final Decision

### Explicit-weight methods only: `MMR + LNS`

| Weight `(w_rouge / w_minicheck / w_redundancy)` | MMR R1 | MMR MiniCheck | MMR FactCC | LNS R1 | LNS MiniCheck | LNS FactCC | Avg R1 | Avg MiniCheck | Avg FactCC | Avg fact_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0.0 / 0.5 / 0.5` | 42.25 | 95.39 | 78.61 | 42.43 | 95.85 | 79.52 | 42.34 | 95.62 | 79.06 | 87.34 |
| `0.0 / 0.3 / 0.7` | 42.05 | 94.94 | 77.68 | 43.36 | 95.84 | 81.85 | 42.71 | 95.39 | 79.77 | 87.58 |
| `0.0 / 0.2 / 0.8` | 41.91 | 94.30 | 78.38 | 43.19 | 95.34 | 80.21 | 42.55 | 94.82 | 79.29 | 87.06 |

Where:

- `Avg fact_mean = (Avg MiniCheck + Avg FactCC) / 2`

## Intermediate Cross-check on `ILP + LNS`

This was used during the process before the scope was narrowed to explicit-weight methods only.

| Weight `(w_rouge / w_minicheck / w_redundancy)` | ILP R1 | ILP MiniCheck | ILP FactCC | LNS R1 | LNS MiniCheck | LNS FactCC | Avg R1 | Avg MiniCheck | Avg FactCC | Avg fact_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0.0 / 0.4 / 0.6` | 41.40 | 94.73 | 78.52 | 43.42 | 95.88 | 80.20 | 42.41 | 95.31 | 79.36 | 87.33 |
| `0.0 / 0.3 / 0.7` | 41.44 | 94.72 | 79.16 | 43.36 | 95.84 | 81.85 | 42.40 | 95.28 | 80.51 | 87.89 |
| `0.0 / 0.2 / 0.8` | 41.54 | 94.23 | 78.74 | 43.19 | 95.34 | 80.21 | 42.37 | 94.79 | 79.47 | 87.13 |

This cross-check also supported shifting more mass from `MiniCheck` to `Redundancy`.

## Final Decision

The final shared weight for the explicit-weight methods was fixed at:

- `w_rouge = 0.0`
- `w_minicheck = 0.3`
- `w_redundancy = 0.7`

### Reason

Under the final scope (`MMR + LNS` only), `0.0 / 0.3 / 0.7` gave the best overall balance:

- highest `Avg R1`
- stronger `FactCC` than `0.0 / 0.5 / 0.5`
- better combined factuality than `0.0 / 0.2 / 0.8`

### Interpretation

For the current setup:

- sentence-level `ROUGE` utility did not provide stable gain, so `w_rouge` was driven to `0`
- the real tradeoff was between `MiniCheck` and `Redundancy`
- the best balance was not extreme `MiniCheck`, but a heavier `Redundancy` setting

## Separate `MBR` Weight Decision

`MBR` was treated separately because it is not the same 3-way explicit-weight form as `MMR` and `LNS`.

In `MBR`:

- the `rouge` slot in the tri-metric interface is actually used as `consensus_weight`
- the `minicheck` slot is used as `minicheck_weight`
- the `redundancy` term is ignored by the current `MBR` implementation

Three validation points were checked:

| Weight `(w_rouge / w_minicheck / w_redundancy)` | R1 | R2 | RL | MiniCheck |
| --- | ---: | ---: | ---: | ---: |
| `0.2 / 0.8 / 0.0` | 39.40 | 18.30 | 28.57 | 96.67 |
| `0.3 / 0.7 / 0.0` | 39.18 | 18.42 | 28.64 | 96.45 |
| `0.4 / 0.6 / 0.0` | 39.52 | 18.78 | 29.03 | 96.42 |

The automatic script ranking by `MiniCheck` picked `0.2 / 0.8 / 0.0`.

For the final record, the adopted `MBR` weight was fixed at:

- `w_rouge = 0.4`
- `w_minicheck = 0.6`
- `w_redundancy = 0.0`

### Reason

`0.4 / 0.6 / 0.0` gave the strongest ROUGE among the three points, while factuality dropped only slightly relative to `0.2 / 0.8 / 0.0`.

## Final Method Settings

The current main-experiment settings are:

| Method or Group | Final Setting |
| --- | --- |
| `MMR` | tri-metric fixed weight `0.0 / 0.3 / 0.7` |
| `ILP` | tri-metric fixed weight `0.0 / 0.3 / 0.7` |
| `LNS` | tri-metric fixed weight `0.0 / 0.3 / 0.7` |
| `MBR` | separate fixed weight `0.4 / 0.6 / 0.0` |
| `DPP` | keep original `minicheck_redundancy` objective |
| `Submodular` | keep original `minicheck_redundancy` objective |
| `Pareto` | keep original method, with current pool size `16` |
| `baseline_raw` | no optimization weight; keep as HF-aligned baseline |

## Files to Keep

Primary summary files:

- `bart/results/tri_metric_weight_search_summary.md`
- `bart/results/tri_metric_weight_search_summary.csv`
- `bart/results/tri_metric_selected_weight_explicit_methods_validation_n50.csv`

Primary result files kept for reference:

- `bart/results/mmr_tri_metric_wr0p00_wm0p50_wd0p50_validation_n50_beam5/beam5_mmr_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/mmr_tri_metric_wr0p00_wm0p30_wd0p70_validation_n50_beam5/beam5_mmr_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/mmr_tri_metric_wr0p00_wm0p20_wd0p80_validation_n50_beam5/beam5_mmr_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/lns_tri_metric_wr0p00_wm0p50_wd0p50_validation_n50_beam5/beam5_lns_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/lns_tri_metric_wr0p00_wm0p30_wd0p70_validation_n50_beam5/beam5_lns_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/lns_tri_metric_wr0p00_wm0p20_wd0p80_validation_n50_beam5/beam5_lns_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/ilp_tri_metric_wr0p00_wm0p40_wd0p60_validation_n50_beam5/beam5_ilp_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/ilp_tri_metric_wr0p00_wm0p30_wd0p70_validation_n50_beam5/beam5_ilp_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
- `bart/results/ilp_tri_metric_wr0p00_wm0p20_wd0p80_validation_n50_beam5/beam5_ilp_tri_metric_hfrouge_validation_shuffle_seed42_results.txt`
