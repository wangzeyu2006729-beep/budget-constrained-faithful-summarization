"""Backward-compat shim — canonical location: metrics/minicheck_eval_utils.py"""
from metrics.minicheck_eval_utils import *  # noqa: F401,F403
from metrics.minicheck_eval_utils import (  # explicit re-exports
    MINICHECK_CACHE_DIR,
    MINICHECK_MODEL_NAME,
    compute_minicheck_sentence_scores,
    compute_minicheck_summary_scores,
    load_minicheck_model,
)
