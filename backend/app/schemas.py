"""Pydantic schemas = the shape of JSON going in and out of the API.

Keeping these separate from ORM models lets you expose only what you want.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from enum import Enum


class TaskCreate(BaseModel):
    title: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: int
    created_at: datetime


# --- /analyse : farm water-use benchmark comparison -------------------------

class IrrigationMethod(str, Enum):
    FLOOD = "flood"
    SPRAY = "spray"
    SPRAY_SOLID_SET = "spray_solid_set"
    DRIP = "drip"
    UNKNOWN = "unknown"


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
    currentIrrigationMethod: IrrigationMethod = IrrigationMethod.UNKNOWN
    budgetAud: float | None = Field(default=None, ge=0)


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


class BusinessData(BaseModel):
    location: LocationIn
    cropCategory: str
    waterUsed: float
    landArea: float
    currentIrrigationMethod: IrrigationMethod = IrrigationMethod.UNKNOWN
    budgetAud: float | None = Field(default=None, ge=0)


class RiskResult(BaseModel):
    z_score: float | None
    risk_level: str
    user_ml_per_ha: float
    benchmark_mean: float | None
    benchmark_std: float | None
    sample_size: int | None
    lls_region: str | None
    valley_name: str | None


class StrategyRecommendation(BaseModel):
    id: str
    name: str
    category: str
    annual_cost_aud: float
    estimated_savings_ml: float
    savings_pct_applied: float
    implementation_disruption: str
    confidence: str
    source: str
 
 
class RecommendationResult(BaseModel):
    risk: RiskResult
    optimization_mode: str
    target_savings_ml: float | None
    budget_aud: float | None
    selected_strategies: list[StrategyRecommendation]
    total_annual_cost_aud: float
    total_estimated_savings_ml: float
    cost_per_ml_saved_aud: float | None
    projected_water_use_ml_per_ha: float
    projected_z_score: float | None
    projected_risk_level: str
    excluded_strategies_note: str
 