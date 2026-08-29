"""Risk scoring helpers for the optimization recommendation pipeline."""

from __future__ import annotations

import math


def compute_z_score(user_ml_per_ha: float, benchmark_mean: float | None, benchmark_std: float | None) -> float | None:
    """Return a standard z-score for a farm's water use vs the benchmark mean/std.

    A single benchmark sample has no meaningful spread, so we treat it as a neutral
    baseline rather than rejecting the recommendation pipeline.
    """
    if benchmark_mean is None or benchmark_std in (None, 0):
        return None

    try:
        spread = float(benchmark_std)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(spread) or spread == 0:
        return None

    return (user_ml_per_ha - float(benchmark_mean)) / spread


def bucket_risk(z_score: float | None) -> str:
    """Convert a z-score into a simplified risk bucket used by the API."""
    if z_score is None:
        return "low"
    if z_score < -1.0:
        return "low"
    if z_score < 1.0:
        return "medium"
    return "high"
