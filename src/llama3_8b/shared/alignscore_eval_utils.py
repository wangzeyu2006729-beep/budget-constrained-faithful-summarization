"""Backward-compat shim — canonical location: metrics/alignscore_eval_utils.py"""
from metrics.alignscore_eval_utils import *  # noqa: F401,F403
from metrics.alignscore_eval_utils import (  # explicit re-exports
    ALIGNSCORE_CKPT,
    ALIGNSCORE_EVAL_MODE,
    ALIGNSCORE_MODEL_NAME,
    ALIGNSCORE_SRC,
    compute_alignscore_summary_scores,
    load_alignscore_model,
)
