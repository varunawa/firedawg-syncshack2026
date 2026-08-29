"""Risk scoring helpers for the optimization recommendation pipeline."""

from __future__ import annotations

import csv
import math
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "water_allocation.csv"

_REGION_TO_WATER_SOURCE = {
    "central_tablelands": {"lachlan"},
    "central_west": {"macquarie"},
    "greater_sydney": {"murray"},
    "hunter": {"murray"},
    "murray": {"murray"},
    "north_coast": {"murray"},
    "north_west_nsw": {"lower_namoi", "namoi"},
    "northern_tablelands": {"gwydir"},
    "riverina": {"murrumbidgee"},
    "south_east_nsw": {"murray"},
    "western": {"lower_darling"},
}


def _water_source_candidates(region: str | None) -> set[str]:
    if not region:
        return set()

    normalized = str(region).strip().lower().replace("_", " ")
    candidates = {normalized.replace(" ", "_")}
    candidates.add(normalized)
    candidates |= _REGION_TO_WATER_SOURCE.get(normalized.replace(" ", "_"), set())
    candidates |= _REGION_TO_WATER_SOURCE.get(normalized, set())
    return {c.strip().lower() for c in candidates if c}


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


def compute_adjusted_risk_score(
    base_score: float | None,
    allocation_factor: float = 1.0,
    rainfall_factor: float = 1.0,
) -> float | None:
    """Scale a benchmark risk score by water-allocation and rainfall stress factors."""
    if base_score is None:
        return None
    try:
        return float(base_score) * float(allocation_factor) * float(rainfall_factor)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=1)
def _water_allocation_rows() -> list[dict[str, str]]:
    if not _DATA_PATH.exists():
        return []

    with _DATA_PATH.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows: list[dict[str, str]] = []
        for row in reader:
            water_source = (row.get("water_source") or "").strip().lower()
            if not water_source:
                continue
            rows.append({
                "water_source": water_source,
                "water_year": (row.get("water_year") or "").strip(),
                "cumulative_allocation_ml_per_share": row.get("cumulative_allocation_ml_per_share") or "0",
            })
    return rows


def estimate_allocation_factor(region: str | None) -> float:
    """Return a multiplier >1.0 when a region is under its historic allocation."""
    if not region:
        return 1.0

    candidates = _water_source_candidates(region)
    rows = [row for row in _water_allocation_rows() if row["water_source"] in candidates]
    if not rows:
        return 1.0

    current_year = max((row["water_year"] for row in rows), default=None)
    if not current_year:
        return 1.0

    current_values = [
        float(row["cumulative_allocation_ml_per_share"])
        for row in rows if row["water_year"] == current_year
    ]
    prior_values = [
        float(row["cumulative_allocation_ml_per_share"])
        for row in rows if row["water_year"] != current_year
    ]
    if not current_values:
        return 1.0

    current_avg = sum(current_values) / len(current_values)
    historical_avg = sum(prior_values) / len(prior_values) if prior_values else current_avg
    if historical_avg <= 0:
        return 1.0

    shortfall = max(0.0, (historical_avg - current_avg) / historical_avg)
    return 1.0 + (shortfall * 1.6)


def estimate_rainfall_factor(weather_summary: dict | None) -> float:
    """Increase risk when rainfall is low or evaporative demand is high."""
    if not weather_summary:
        return 1.0

    rainfall_mm = float(weather_summary.get("seven_day_rainfall_mm") or 0.0)
    deficit_mm = float(weather_summary.get("climatic_water_deficit_mm") or 0.0)

    rain_pressure = max(0.0, (30.0 - rainfall_mm) / 30.0)
    deficit_pressure = max(0.0, (deficit_mm - 25.0) / 25.0)
    return 1.0 + (rain_pressure * 0.8) + (deficit_pressure * 0.5)


def classify_weather_status(weather_summary: dict | None) -> str:
    """Return a human-readable weather condition label for the snapshot UI."""
    if not weather_summary:
        return "weather unavailable"

    rainfall_mm = float(weather_summary.get("seven_day_rainfall_mm") or 0.0)
    deficit_mm = float(weather_summary.get("climatic_water_deficit_mm") or 0.0)

    if rainfall_mm < 10 and deficit_mm > 25:
        return "dry"
    if rainfall_mm < 25:
        return "low rain"
    if rainfall_mm < 50:
        return "moderate rain"
    return "rainy"


def water_allocation_context(region: str | None) -> dict[str, float | str | None]:
    """Return water source and historic-vs-current allocation status for display."""
    if not region:
        return {"water_source": None, "current_allocation": None, "historic_allocation": None, "pct_vs_historic": None}

    normalized = str(region).strip().lower().replace("_", " ")
    candidates = _water_source_candidates(region)
    rows = [row for row in _water_allocation_rows() if row["water_source"] in candidates]
    if not rows:
        water_source = normalized.title().replace(" ", " ")
        return {"water_source": water_source, "current_allocation": None, "historic_allocation": None, "pct_vs_historic": None}

    current_year = max((row["water_year"] for row in rows), default=None)
    if not current_year:
        water_source = next(iter(candidates), normalized).title().replace("_", " ")
        return {"water_source": water_source, "current_allocation": None, "historic_allocation": None, "pct_vs_historic": None}

    current_values = [
        float(row["cumulative_allocation_ml_per_share"])
        for row in rows if row["water_year"] == current_year
    ]
    prior_values = [
        float(row["cumulative_allocation_ml_per_share"])
        for row in rows if row["water_year"] != current_year
    ]

    if not current_values:
        return {"water_source": normalized.title(), "current_allocation": None, "historic_allocation": None, "pct_vs_historic": None}

    current_avg = sum(current_values) / len(current_values)
    historical_avg = sum(prior_values) / len(prior_values) if prior_values else current_avg
    if historical_avg <= 0:
        pct_vs_historic = 0.0
    else:
        pct_vs_historic = ((current_avg / historical_avg) - 1.0) * 100.0

    water_source_value = next(iter(candidates), normalized).replace("_", " ").title()
    return {
        "water_source": water_source_value,
        "current_allocation": round(current_avg, 3),
        "historic_allocation": round(historical_avg, 3),
        "pct_vs_historic": round(pct_vs_historic, 1),
    }


def bucket_risk(z_score: float | None, adjustment_factor: float = 1.0) -> str:
    """Convert a z-score into a simplified risk bucket used by the API."""
    effective_score = z_score * adjustment_factor if z_score is not None else None
    if effective_score is None:
        return "low"
    if effective_score < -1.0:
        return "low"
    if effective_score < 1.0:
        return "medium"
    return "high"
