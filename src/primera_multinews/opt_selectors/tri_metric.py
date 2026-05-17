"""Helpers for the tri-metric unified objective."""

from __future__ import annotations


TRI_TOLERANCE = 1e-6


def tri_metric_utility(rouge_score: float, minicheck_score: float, w_rouge: float, w_minicheck: float) -> float:
    """Return the utility term without redundancy."""
    return float(w_rouge) * float(rouge_score) + float(w_minicheck) * float(minicheck_score)


def normalize_tri_metric_weights(
    w_rouge: float,
    w_minicheck: float,
    w_redundancy: float,
) -> tuple[dict[str, float], bool]:
    """Return raw non-negative tri-metric weights without sum normalization."""
    weights = {
        "rouge": max(0.0, float(w_rouge)),
        "minicheck": max(0.0, float(w_minicheck)),
        "redundancy": max(0.0, float(w_redundancy)),
    }
    total = sum(weights.values())
    if total <= TRI_TOLERANCE:
        raise ValueError("Tri-metric weights must sum to a positive value.")

    return weights, False


def redundancy_weight_to_lambda(redundancy_weight: float) -> float:
    """Map redundancy weight to the MMR relevance coefficient."""
    return min(1.0, max(0.0, 1.0 - float(redundancy_weight)))


def redundancy_weight_to_threshold(
    redundancy_weight: float,
    low: float = 0.4,
    high: float = 0.8,
) -> float:
    """Map redundancy weight to an ILP similarity threshold."""
    clipped = min(1.0, max(0.0, float(redundancy_weight)))
    return high - (high - low) * clipped


def scale_pairwise_matrix(pairwise_matrix, redundancy_weight: float):
    """Scale off-diagonal similarity entries while keeping the diagonal at 1."""
    clipped = min(1.0, max(0.0, float(redundancy_weight)))
    scaled = []
    for row_index, row in enumerate(pairwise_matrix):
        scaled_row = []
        for col_index, value in enumerate(row):
            if row_index == col_index:
                scaled_row.append(1.0)
            else:
                scaled_row.append(float(value) * clipped)
        scaled.append(scaled_row)
    return scaled


def weighted_tri_metric_score(
    rouge_score: float,
    minicheck_score: float,
    redundancy_score: float,
    weights: dict[str, float],
) -> float:
    """Scalarize the tri-metric objective with redundancy as a penalty."""
    return (
        float(weights["rouge"]) * float(rouge_score)
        + float(weights["minicheck"]) * float(minicheck_score)
        - float(weights["redundancy"]) * float(redundancy_score)
    )
