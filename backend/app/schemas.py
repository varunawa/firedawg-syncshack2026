"""Pydantic schemas = the shape of JSON going in and out of the API.

Keeping these separate from ORM models lets you expose only what you want.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: int
    created_at: datetime


# --- /analyse : farm water-use benchmark comparison -------------------------

class LocationIn(BaseModel):
    postcode: str | int
    suburb: str | None = None
    state: str | None = None
    region_id: str | None = None
    VALLEY_NAME: str | None = None


class AnalyseIn(BaseModel):
    location: LocationIn
    cropCategory: str
    waterUsed: float          # total megalitres applied last year
    landArea: float           # irrigated hectares operated


class BenchmarkResult(BaseModel):
    crop_category: str
    lls_region: str | None
    region_used: str | None            # region the benchmark figure came from
    user_water_intensity_ml_per_ha: float
    benchmark_water_intensity_ml_per_ha: float | None
    benchmark_year: str | None
    is_state_fallback: bool
    delta_pct: float | None            # user vs benchmark, % (+ = uses more)
    z_score: float | None              # vs all NSW regions growing this crop
    percentile: float | None
    sample_size: int | None
    mean_ml_per_ha: float | None
    stdev_ml_per_ha: float | None
    rating: str                        # efficient | typical | high water use | unknown
    note: str | None


class AnalyseOut(BaseModel):
    success: bool
    benchmark: BenchmarkResult


class ExplainOut(BaseModel):
    success: bool
    explanation: str | None   # null when no API key is set or the call failed
