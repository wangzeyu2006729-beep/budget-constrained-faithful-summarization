"""Backward-compat shim — canonical location: opt_selectors/sentence_level/mmr.py"""
from opt_selectors.sentence_level.mmr import mmr_select  # noqa: F401

__all__ = ["mmr_select"]
