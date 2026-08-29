"""Compare a farm's water intensity against the NSW agricultural benchmark.

Data source: ``data/MASTER_CROP.csv`` (ABS Water Use on Australian Farms),
one row per year x region x crop category with a
``water_intensity_ml_per_ha`` figure (megalitres of water applied per
hectare of irrigated land).

Everything here is pure: CSV in, numbers out. No FastAPI, no DB.
"""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.lls_regions import resolve_lls_region

_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "MASTER_CROP.csv"

_STATE_REGION = "New South Wales"

# z-score thresholds (lower intensity = more efficient = better)
_EFFICIENT_MAX_Z = -0.5
_HIGH_MIN_Z = 0.5


@dataclass(frozen=True)
class CropRow:
    year: str
    region_type: str
    region: str
    crop_category: str
    water_intensity: float | None


@lru_cache(maxsize=1)
def _rows() -> list[CropRow]:
    with _DATA_PATH.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        out: list[CropRow] = []
        for r in reader:
            raw = (r.get("water_intensity_ml_per_ha") or "").strip()
            try:
                intensity = float(raw) if raw else None
            except ValueError:
                intensity = None
            out.append(
                CropRow(
                    year=(r.get("year") or "").strip(),
                    region_type=(r.get("region_type") or "").strip(),
                    region=(r.get("region") or "").strip(),
                    crop_category=(r.get("crop_category") or "").strip(),
                    water_intensity=intensity,
                )
            )
    return out


def available_crop_categories() -> list[str]:
    return sorted({row.crop_category for row in _rows() if row.crop_category})


def _latest(rows: list[CropRow]) -> CropRow | None:
    rows = [r for r in rows if r.water_intensity is not None]
    return max(rows, key=lambda r: r.year) if rows else None


@dataclass(frozen=True)
class Benchmark:
    crop_category: str
    region_requested: str | None
    region_used: str | None
    water_intensity_ml_per_ha: float | None
    year: str | None
    is_state_fallback: bool
    note: str | None


def regional_benchmark(region: str | None, crop_category: str) -> Benchmark:
    """Benchmark intensity for a region + crop.

    Uses the most recent year with data. Falls back to the NSW state-wide
    figure when the region is unknown or has no data for that crop.
    """
    crop_rows = [r for r in _rows() if r.crop_category == crop_category]
    if not crop_rows:
        return Benchmark(crop_category, region, None, None, None, False,
                         "No benchmark data for this crop category.")

    if region:
        match = _latest([r for r in crop_rows if r.region == region
                         and r.region_type == "NRM"])
        if match:
            return Benchmark(crop_category, region, region,
                             match.water_intensity, match.year, False, None)

    state = _latest([r for r in crop_rows if r.region == _STATE_REGION])
    if state:
        note = (
            f"No regional figure for {region}; using the NSW state-wide benchmark."
            if region else
            "Region could not be determined; using the NSW state-wide benchmark."
        )
        return Benchmark(crop_category, region, _STATE_REGION,
                         state.water_intensity, state.year, True, note)

    return Benchmark(crop_category, region, None, None, None, False,
                     "No benchmark data available for this crop category.")


def crop_distribution(crop_category: str) -> list[float]:
    """Every regional intensity for a crop (all NRM regions, all years).

    This is the reference population for the z-score: how one farm's water
    intensity compares to NSW regions growing the same crop.
    """
    return [
        r.water_intensity
        for r in _rows()
        if r.crop_category == crop_category
        and r.region_type == "NRM"
        and r.water_intensity is not None
    ]


@dataclass(frozen=True)
class ZScore:
    mean: float
    stdev: float
    z: float | None
    percentile: float
    sample_size: int


def z_score(value: float, population: list[float]) -> ZScore | None:
    """z-score of ``value`` against ``population`` (needs >= 2 points)."""
    n = len(population)
    if n < 2:
        return None
    mean = statistics.fmean(population)
    stdev = statistics.stdev(population)
    z = (value - mean) / stdev if stdev > 0 else None
    at_or_below = sum(1 for p in population if p <= value)
    percentile = round(100 * at_or_below / n, 1)
    return ZScore(round(mean, 3), round(stdev, 3),
                  round(z, 2) if z is not None else None, percentile, n)


def _rating(z: float | None) -> str:
    if z is None:
        return "unknown"
    if z <= _EFFICIENT_MAX_Z:
        return "efficient"
    if z >= _HIGH_MIN_Z:
        return "high water use"
    return "typical"


@dataclass(frozen=True)
class Comparison:
    crop_category: str
    lls_region: str | None
    region_used: str | None
    user_water_intensity_ml_per_ha: float
    benchmark_water_intensity_ml_per_ha: float | None
    benchmark_year: str | None
    is_state_fallback: bool
    delta_pct: float | None
    z_score: float | None
    percentile: float | None
    sample_size: int | None
    mean_ml_per_ha: float | None
    stdev_ml_per_ha: float | None
    rating: str
    note: str | None
    allocation_factor: float | None = None
    rainfall_factor: float | None = None
    adjusted_risk_score: float | None = None
    risk_drivers: list[str] | None = None
    water_source: str | None = None
    water_allocation_pct_vs_historic: float | None = None
    weather_status: str | None = None
    weather_summary: dict | None = None


def compare(
    *,
    postcode: str | int | None,
    lls_region: str | None,
    crop_category: str,
    water_used_ml: float,
    land_area_ha: float,
    allocation_factor: float | None = None,
    rainfall_factor: float | None = None,
    adjusted_risk_score: float | None = None,
    risk_drivers: list[str] | None = None,
    water_source: str | None = None,
    water_allocation_pct_vs_historic: float | None = None,
    weather_status: str | None = None,
    weather_summary: dict | None = None,
) -> Comparison:
    """Full benchmark comparison for one farm's inputs."""
    if land_area_ha <= 0:
        raise ValueError("land_area_ha must be greater than 0")
    if water_used_ml < 0:
        raise ValueError("water_used_ml cannot be negative")

    region = lls_region
    if region is None and postcode is not None:
        region = resolve_lls_region(postcode)

    user_intensity = round(water_used_ml / land_area_ha, 3)
    bench = regional_benchmark(region, crop_category)

    delta_pct = None
    if bench.water_intensity_ml_per_ha:
        delta_pct = round(
            100 * (user_intensity - bench.water_intensity_ml_per_ha)
            / bench.water_intensity_ml_per_ha,
            1,
        )

    zs = z_score(user_intensity, crop_distribution(crop_category))

    return Comparison(
        crop_category=crop_category,
        lls_region=region,
        region_used=bench.region_used,
        user_water_intensity_ml_per_ha=user_intensity,
        benchmark_water_intensity_ml_per_ha=bench.water_intensity_ml_per_ha,
        benchmark_year=bench.year,
        is_state_fallback=bench.is_state_fallback,
        delta_pct=delta_pct,
        z_score=zs.z if zs else None,
        percentile=zs.percentile if zs else None,
        sample_size=zs.sample_size if zs else None,
        mean_ml_per_ha=zs.mean if zs else None,
        stdev_ml_per_ha=zs.stdev if zs else None,
        rating=_rating(zs.z if zs else None),
        note=bench.note,
        allocation_factor=allocation_factor,
        rainfall_factor=rainfall_factor,
        adjusted_risk_score=adjusted_risk_score,
        risk_drivers=risk_drivers,
        water_source=water_source,
        water_allocation_pct_vs_historic=water_allocation_pct_vs_historic,
        weather_status=weather_status,
        weather_summary=weather_summary,
    )
