"""Backward-compat shim — canonical location: metrics/evaluation.py"""
from metrics.evaluation import *  # noqa: F401,F403
from metrics.evaluation import (  # explicit re-exports
    SUPPORTED_METRIC_NAMES,
    compute_moverscore,
    normalize_metric_names,
    run_all_evaluations,
    split_sentences_for_rouge,
)
