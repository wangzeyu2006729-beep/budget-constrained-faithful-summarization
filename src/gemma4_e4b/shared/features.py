"""Backward-compat shim — canonical location: core/features.py"""
from core.features import *  # noqa: F401,F403
from core.features import (  # explicit re-exports
    build_sentence_pool,
    compute_minicheck_utility_scores,
    compute_redundancy_matrix,
    compute_rouge_utility_scores,
    compute_tri_metric_utility_scores,
    compute_utility_scores,
    feature_rouge_scorer,
    load_utility_model,
)
