from fastapi import APIRouter, Depends, HTTPException

from app.schemas import BusinessData, RecommendationResult, StrategyRecommendation, RiskResult
from app.services.data_loader import RiskDataStore, get_data_store
from app.services.strategy_loader import StrategyCatalog, get_strategy_catalog
from app.services.optimizer import select_optimal_strategies, OptimizationResult
from app.services.projection import build_projection
from app.services.risk import (
    bucket_risk,
    compute_adjusted_risk_score,
    compute_z_score,
    estimate_allocation_factor,
    estimate_rainfall_factor,
)
from app.services.weather import geocode_location, get_weather_data

router = APIRouter()


def _target_savings_ml(user_ml_per_ha: float, mean: float, std: float,
                        land_area: float, risk_level: str) -> float | None:
    if risk_level not in ("medium", "high") or std is None or std == 0:
        return None
    threshold_sigma = 1.0 if risk_level == "medium" else 2.0
    target_ml_per_ha = mean + threshold_sigma * std
    if user_ml_per_ha <= target_ml_per_ha:
        return None
    return (user_ml_per_ha - target_ml_per_ha) * land_area


@router.post("/recommend-strategies", response_model=RecommendationResult)
async def recommend_strategies(
    data: BusinessData,
    store: RiskDataStore = Depends(get_data_store),
    catalog: StrategyCatalog = Depends(get_strategy_catalog),
):
    if data.landArea <= 0:
        raise HTTPException(400, "landArea must be > 0")

    user_ml_per_ha = data.waterUsed / data.landArea

    if not data.location.suburb:
        raise HTTPException(400, "Suburb is required.")

    lls_info = store.lookup_lls(
        str(data.location.postcode),
        data.location.suburb,
    )
    
    if lls_info is None:
        raise HTTPException(404, f"No LLS mapping found for suburb '{data.location.suburb}'")

    stats = store.lookup_crop_stats(lls_info["region_id"], data.cropCategory)
    if stats is None or stats["n"] < 1:
        raise HTTPException(422, "Insufficient benchmark data for this LLS/crop combination.")

    weather_summary = None
    if data.location.suburb:
        place_name = ", ".join(part for part in [data.location.suburb, data.location.state or "NSW"] if part)
        try:
            geo = await geocode_location(place_name)
            weather = await get_weather_data(geo["latitude"], geo["longitude"])
            weather_summary = weather.get("summary")
        except Exception:
            weather_summary = None

    allocation_factor = estimate_allocation_factor(lls_info["region_id"])
    rainfall_factor = estimate_rainfall_factor(weather_summary)

    z = compute_z_score(user_ml_per_ha, stats["mean"], stats["std"])
    adjusted_risk_score = compute_adjusted_risk_score(z, allocation_factor, rainfall_factor)
    risk_level = bucket_risk(z, allocation_factor * rainfall_factor)

    risk_drivers: list[str] = []
    if allocation_factor > 1.0:
        risk_drivers.append(f"Water allocation is running below the region's recent historic level ({allocation_factor:.2f}x stress factor).")
    if rainfall_factor > 1.0:
        risk_drivers.append(
            f"Rainfall and evaporative demand are creating dry conditions ({rainfall_factor:.2f}x stress factor)."
        )

    risk = RiskResult(
        z_score=z,
        risk_score=adjusted_risk_score,
        risk_level=risk_level,
        user_ml_per_ha=user_ml_per_ha,
        benchmark_mean=stats["mean"],
        benchmark_std=stats["std"],
        sample_size=stats["n"],
        lls_region=lls_info["region_id"],
        valley_name=lls_info["valley_name"],
        allocation_factor=allocation_factor,
        rainfall_factor=rainfall_factor,
        risk_drivers=risk_drivers,
    )

    target_ml = _target_savings_ml(user_ml_per_ha, stats["mean"], stats["std"], data.landArea, risk_level)

    candidates = catalog.candidates_for_farm(
        crop_category=data.cropCategory,
        current_irrigation=data.currentIrrigationMethod.value,
        user_ml_per_ha=user_ml_per_ha,
        land_area_ha=data.landArea,
    )

    if target_ml is not None:
        mode = "minimize_cost_to_target"
        opt = select_optimal_strategies(candidates, mode=mode, target_savings_ml=target_ml)
    elif data.budgetAud is not None:
        mode = "maximize_savings_within_budget"
        opt = select_optimal_strategies(candidates, mode=mode, budget_aud=data.budgetAud)
    else:
        ranked = sorted(candidates, key=lambda s: s.annual_cost_aud / s.savings_ml if s.savings_ml > 0 else float("inf"))
        mode = "ranked_no_constraint"
        opt = OptimizationResult(
            success=True, message="no budget/target given — ranked by cost per ML saved",
            selected=ranked,
            total_cost_aud=sum(s.annual_cost_aud for s in ranked),
            total_savings_ml=sum(s.savings_ml for s in ranked),
        )

    total_savings = sum(s.savings_ml for s in opt.selected) if mode != "ranked_no_constraint" else 0.0
    total_cost = sum(s.annual_cost_aud for s in opt.selected) if mode != "ranked_no_constraint" else 0.0

    projected_ml = max(data.waterUsed - total_savings, 0.0)
    projected_ml_per_ha = projected_ml / data.landArea
    projected_z = compute_z_score(projected_ml_per_ha, stats["mean"], stats["std"])
    projected_risk = bucket_risk(projected_z)

    cost_per_ml = (total_cost / total_savings) if total_savings > 0 else None

    projection = build_projection(
    current_water_intensity_ml_per_ha=user_ml_per_ha,
    projected_water_intensity_ml_per_ha=projected_ml_per_ha,
    total_estimated_savings_ml=total_savings,
    total_annual_cost_aud=total_cost,
    cost_per_ml_saved_aud=cost_per_ml,
    land_area_ha=data.landArea,
)

    return RecommendationResult(
        risk=risk,
        optimization_mode=mode,
        target_savings_ml=target_ml,
        budget_aud=data.budgetAud,
        selected_strategies=[
            StrategyRecommendation(
                id=s.id, name=s.name, category=s.category,
                annual_cost_aud=s.annual_cost_aud, estimated_savings_ml=s.savings_ml,
                savings_pct_applied=s.savings_pct_applied,
                implementation_disruption=s.implementation_disruption,
                confidence=s.confidence, source=s.source,
            )
            for s in opt.selected
        ],
        total_annual_cost_aud=round(total_cost, 2),
        total_estimated_savings_ml=round(total_savings, 3),
        cost_per_ml_saved_aud=round(cost_per_ml, 2) if cost_per_ml else None,
        projected_water_use_ml_per_ha=round(projected_ml_per_ha, 3),
        projected_z_score=projected_z,
        projected_risk_level=projected_risk,
        excluded_strategies_note=opt.message if not opt.success else "",
        projection=projection,
    )