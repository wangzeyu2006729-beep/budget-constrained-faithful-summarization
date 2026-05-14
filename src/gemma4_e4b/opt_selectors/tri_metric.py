"""Helpers for the Week 10 tri-metric unified objective."""

from __future__ import annotations

from bisect import bisect_right
import json
from pathlib import Path


TRI_TOLERANCE = 1e-6


def tri_metric_utility(rouge_score: float, minicheck_score: float, w_rouge: float, w_minicheck: float) -> float:
    """Return the utility term without redundancy."""
    return float(w_rouge) * float(rouge_score) + float(w_minicheck) * float(minicheck_score)


class RobustPercentileMinMaxCalibrator:
    """Map heterogeneous tri-metric scores to [0, 1] using robust min-max normalization based on q05 and q95 percentiles."""

    REQUIRED_DISTRIBUTIONS = ("coverage", "faithfulness", "redundancy")

    def __init__(
        self,
        summary: dict,
        source_path: str | None = None,
        redundancy_gamma: float = 2.0,
    ):
        self.bounds = {}
        for name in self.REQUIRED_DISTRIBUTIONS:
            dist_summary = summary.get(name, {})
            p_lo = dist_summary.get("q05")
            p_hi = dist_summary.get("q95")
            if p_lo is None or p_hi is None:
                raise ValueError(f"Missing q05 or q95 for {name} in calibration summary.")
            self.bounds[name] = {"p_lo": float(p_lo), "p_hi": float(p_hi)}
            
        self.source_path = source_path
        self.summary = dict(summary)
        self.redundancy_gamma = max(0.0, float(redundancy_gamma))

    @classmethod
    def from_json(cls, path: str | Path, redundancy_gamma: float = 2.0) -> "RobustPercentileMinMaxCalibrator":
        path = Path(path).expanduser().resolve()
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return cls(
            summary=payload.get("summary", {}),
            source_path=str(path),
            redundancy_gamma=redundancy_gamma,
        )

    def _normalize(self, distribution_name: str, value: float) -> float:
        bounds = self.bounds[distribution_name]
        p_lo = bounds["p_lo"]
        p_hi = bounds["p_hi"]
        if p_hi <= p_lo:
            return 0.0
        normalized = (float(value) - p_lo) / (p_hi - p_lo)
        return min(1.0, max(0.0, normalized))

    def calibrate_values(self, distribution_name: str, values) -> list[float]:
        return [self._normalize(distribution_name, value) for value in values]

    def calibrate_redundancy_matrix(self, matrix) -> list[list[float]]:
        calibrated = []
        for row_index, row in enumerate(matrix):
            calibrated_row = []
            for col_index, value in enumerate(row):
                if row_index == col_index:
                    calibrated_row.append(1.0)
                else:
                    redundancy_normalized = self._normalize("redundancy", value)
                    calibrated_row.append(redundancy_normalized ** self.redundancy_gamma)
            calibrated.append(calibrated_row)
        return calibrated

    def metadata(self) -> dict:
        return {
            "method": "robust_percentile_min_max",
            "source_path": self.source_path,
            "coverage_transform": "robust_min_max_q05_q95",
            "faithfulness_transform": "robust_min_max_q05_q95",
            "redundancy_transform": "robust_min_max_q05_q95_power",
            "redundancy_gamma": self.redundancy_gamma,
            "summary": self.summary,
            "bounds": self.bounds,
        }


def load_tri_metric_calibrator(path: str | Path | None, redundancy_gamma: float = 2.0):
    if not path:
        return None
    return RobustPercentileMinMaxCalibrator.from_json(path, redundancy_gamma=redundancy_gamma)


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
    """Map redundancy weight to an ILP/LNS similarity threshold."""
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
