"""Beam-search helpers aligned with Hugging Face BART generation.

The project-specific difference from the standalone HF baseline is the beam
width. All other decode parameters should come from the checkpoint's official
`generation_config`.
"""

from __future__ import annotations

import os

import torch
from transformers.modeling_outputs import BaseModelOutput

from core.config import LENGTH_PENALTY, MAX_DECODE_STEPS, MIN_DECODE_STEPS, NO_REPEAT_NGRAM


_GROUP_BEAM_REPO_ID = "transformers-community/group-beam-search"
_group_beam_local_snapshot: str | None = None


def _resolve_group_beam_custom_generate() -> str:
    global _group_beam_local_snapshot

    if _group_beam_local_snapshot and os.path.isdir(_group_beam_local_snapshot):
        return _group_beam_local_snapshot

    try:
        from huggingface_hub import snapshot_download

        _group_beam_local_snapshot = snapshot_download(
            repo_id=_GROUP_BEAM_REPO_ID,
            allow_patterns=["custom_generate/*", "README.md", "config.json"],
        )
        return _group_beam_local_snapshot
    except Exception:
        return _GROUP_BEAM_REPO_ID


def _resolve_generation_kwargs(model, beam_size: int) -> dict:
    generation_config = model.generation_config
    decoder_start_token_id = generation_config.decoder_start_token_id
    if decoder_start_token_id is None:
        decoder_start_token_id = model.config.decoder_start_token_id

    return {
        "num_beams": beam_size,
        "num_return_sequences": beam_size,
        "max_length": generation_config.max_length or MAX_DECODE_STEPS,
        "min_length": generation_config.min_length or MIN_DECODE_STEPS,
        "length_penalty": generation_config.length_penalty or LENGTH_PENALTY,
        "no_repeat_ngram_size": generation_config.no_repeat_ngram_size or NO_REPEAT_NGRAM,
        "early_stopping": True if generation_config.early_stopping is None else generation_config.early_stopping,
        "use_cache": True,
        "return_dict_in_generate": True,
        "output_scores": True,
        "decoder_start_token_id": decoder_start_token_id,
        "forced_bos_token_id": generation_config.forced_bos_token_id,
        "forced_eos_token_id": generation_config.forced_eos_token_id,
        "bos_token_id": generation_config.bos_token_id,
        "eos_token_id": generation_config.eos_token_id,
        "pad_token_id": generation_config.pad_token_id,
    }


def _encoder_output_beam_search_decode(model, encoder_output, encoder_mask, beam_size):
    generation_kwargs = _resolve_generation_kwargs(model, beam_size)
    with torch.no_grad():
        generated = model.generate(
            encoder_outputs=BaseModelOutput(last_hidden_state=encoder_output),
            attention_mask=encoder_mask,
            **generation_kwargs,
        )

    sequence_scores = generated.sequences_scores
    if sequence_scores is None:
        sequence_scores = torch.zeros(generated.sequences.size(0), device=generated.sequences.device)

    return [
        (float(score), token_ids)
        for score, token_ids in zip(sequence_scores.tolist(), generated.sequences.tolist())
    ]


def _input_beam_search_decode(model, input_ids, attention_mask, beam_size):
    generation_kwargs = _resolve_generation_kwargs(model, beam_size)
    with torch.no_grad():
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **generation_kwargs,
        )

    sequence_scores = generated.sequences_scores
    if sequence_scores is None:
        sequence_scores = torch.zeros(generated.sequences.size(0), device=generated.sequences.device)

    return [
        (float(score), token_ids)
        for score, token_ids in zip(sequence_scores.tolist(), generated.sequences.tolist())
    ]


def batch_beam_search_decode(model, input_ids, attention_mask, beam_size):
    """Return beam candidates grouped by sample for a batched input tensor."""
    generation_kwargs = _resolve_generation_kwargs(model, beam_size)
    with torch.no_grad():
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **generation_kwargs,
        )

    sequence_scores = generated.sequences_scores
    if sequence_scores is None:
        sequence_scores = torch.zeros(generated.sequences.size(0), device=generated.sequences.device)

    flat_candidates = [
        (float(score), token_ids)
        for score, token_ids in zip(sequence_scores.tolist(), generated.sequences.tolist())
    ]

    batch_size = int(input_ids.size(0))
    if batch_size <= 1:
        return [flat_candidates]

    grouped_candidates = []
    for start in range(0, len(flat_candidates), beam_size):
        grouped_candidates.append(flat_candidates[start:start + beam_size])
    return grouped_candidates


def beam_search_decode(model, *args):
    """Return top beam candidates as `(score, token_ids)` tuples.

    Supports both call styles:
    - encoder-output compatibility path: `(encoder_output, encoder_mask, tokenizer, device, beam_size)`
    - reproduction helpers: `(input_ids, attention_mask, beam_size)`
    """
    if len(args) == 5:
        encoder_output, encoder_mask, tokenizer, device, beam_size = args
        del tokenizer, device
        if beam_size < 1:
            raise ValueError(f"beam_size must be >= 1, got {beam_size}.")
        return _encoder_output_beam_search_decode(model, encoder_output, encoder_mask, beam_size)

    if len(args) == 3:
        input_ids, attention_mask, beam_size = args
        if beam_size < 1:
            raise ValueError(f"beam_size must be >= 1, got {beam_size}.")
        return _input_beam_search_decode(model, input_ids, attention_mask, beam_size)

    raise TypeError("beam_search_decode expects either 3 or 5 positional arguments after model.")


def diverse_beam_search_decode(model, input_ids, attention_mask, num_candidates, num_beam_groups=None, diversity_penalty=1.0):
    """Return diverse beam candidates as `(score, token_ids)` tuples."""
    if num_candidates < 2:
        return _input_beam_search_decode(model, input_ids, attention_mask, num_candidates)

    if num_beam_groups is None:
        num_beam_groups = num_candidates

    generation_kwargs = _resolve_generation_kwargs(model, num_candidates)

    with torch.no_grad():
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            num_beam_groups=num_beam_groups,
            diversity_penalty=diversity_penalty,
            custom_generate=_resolve_group_beam_custom_generate(),
            trust_remote_code=True,
            **generation_kwargs,
        )

    sequence_scores = generated.sequences_scores
    if sequence_scores is None:
        sequence_scores = torch.zeros(generated.sequences.size(0), device=generated.sequences.device)

    return [
        (float(score), token_ids)
        for score, token_ids in zip(sequence_scores.tolist(), generated.sequences.tolist())
    ]
