"""Backward-compat shim — canonical location: core/beam_search.py"""
from core.beam_search import *  # noqa: F401,F403
from core.beam_search import (  # explicit re-exports
    beam_search_decode,
    diverse_beam_search_decode,
)
