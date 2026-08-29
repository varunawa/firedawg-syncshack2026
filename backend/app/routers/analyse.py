"""/analyse -- benchmark a farm's water use against the NSW crop dataset."""

from fastapi import APIRouter, HTTPException

from app.core.benchmark import Comparison, compare
from app.core.lls_regions import resolve_lls_region
from app.schemas import AnalyseIn, AnalyseOut, BenchmarkResult, ExplainOut
from app.services.explainer import explain_comparison
from app.services.risk import (
    classify_weather_status,
    compute_adjusted_risk_score,
    estimate_allocation_factor,
    estimate_rainfall_factor,
    water_allocation_context,
)
from app.services.weather import geocode_location, get_weather_data

router = APIRouter()


async def _environmental_risk(data: AnalyseIn) -> tuple[float, float, list[str], dict | None, str | None, str | None, float | None]:
    region = data.location.region_id or resolve_lls_region(data.location.postcode)
    allocation_context = water_allocation_context(region)
    allocation_factor = estimate_allocation_factor(region)

    weather_summary = None
    if data.location.suburb:
        place_name = ", ".join(
            part for part in [data.location.suburb, data.location.state or "NSW"] if part
        )
        try:
            geo = await geocode_location(place_name)
            weather = await get_weather_data(geo["latitude"], geo["longitude"])
            weather_summary = weather.get("summary")
        except Exception:
            weather_summary = None

    rainfall_factor = estimate_rainfall_factor(weather_summary)
    weather_status = classify_weather_status(weather_summary)
    water_source = allocation_context.get("water_source")
    water_allocation_pct = allocation_context.get("pct_vs_historic")

    risk_drivers: list[str] = []
    if allocation_factor > 1.0:
        risk_drivers.append(
            f"Water allocation is running below recent historic levels ({allocation_factor:.2f}x stress factor)."
        )
    if rainfall_factor > 1.0:
        risk_drivers.append(
            f"Recent rainfall and evaporative demand are creating dry conditions ({rainfall_factor:.2f}x stress factor)."
        )

    return allocation_factor, rainfall_factor, risk_drivers, weather_summary, weather_status, water_source, water_allocation_pct


async def _run_comparison(data: AnalyseIn) -> Comparison:
    try:
        region = data.location.region_id or resolve_lls_region(data.location.postcode)
        allocation_factor, rainfall_factor, risk_drivers, weather_summary, weather_status, water_source, water_allocation_pct = await _environmental_risk(data)
        result = compare(
            postcode=data.location.postcode,
            lls_region=region,
            crop_category=data.cropCategory,
            water_used_ml=data.waterUsed,
            land_area_ha=data.landArea,
            allocation_factor=allocation_factor,
            rainfall_factor=rainfall_factor,
            risk_drivers=risk_drivers,
            water_source=water_source,
            water_allocation_pct_vs_historic=water_allocation_pct,
            weather_status=weather_status,
            weather_summary=weather_summary,
        )
        adjusted_risk_score = compute_adjusted_risk_score(
            result.z_score,
            allocation_factor=allocation_factor,
            rainfall_factor=rainfall_factor,
        )
        return Comparison(
            **{**vars(result), "adjusted_risk_score": adjusted_risk_score, "risk_drivers": risk_drivers}
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analyse", response_model=AnalyseOut, tags=["analyse"])
async def analyse_business(data: AnalyseIn) -> AnalyseOut:
    result = await _run_comparison(data)
    return AnalyseOut(success=True, benchmark=BenchmarkResult(**vars(result)))


@router.post("/analyse/explain", response_model=ExplainOut, tags=["analyse"])
async def explain_business(data: AnalyseIn) -> ExplainOut:
    """Plain-English summary of the benchmark result (calls Claude).

    Call this after /analyse so the stats render immediately and the summary
    fills in a moment later. Returns explanation: null if the LLM is
    unconfigured or unavailable -- never fails the request for that reason.
    """
    result = await _run_comparison(data)
    return ExplainOut(success=True, explanation=explain_comparison(result))
