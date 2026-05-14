"""Backward-compat shim — canonical location: metrics/factcc_eval_utils.py"""
from metrics.factcc_eval_utils import *  # noqa: F401,F403
from metrics.factcc_eval_utils import (  # explicit re-exports
    FACTCC_MODEL_NAME,
    compute_factcc_sentence_scores,
    compute_factcc_summary_scores,
    load_factcc_eval_model,
)
