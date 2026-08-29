from fastapi import APIRouter, Depends, HTTPException

from app.schemas import BusinessData, RecommendationResult, StrategyRecommendation, RiskResult
from app.services.data_loader import RiskDataStore, get_data_store
from app.services.strategy_loader import StrategyCatalog, get_strategy_catalog
from app.services.optimizer import select_optimal_strategies, OptimizationResult
from app.services.risk import compute_z_score, bucket_risk

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
def recommend_strategies(
    data: BusinessData,
    store: RiskDataStore = Depends(get_data_store),
    catalog: StrategyCatalog = Depends(get_strategy_catalog),
):
    if data.landArea <= 0:
        raise HTTPException(400, "landArea must be > 0")

    user_ml_per_ha = data.waterUsed / data.landArea

    lls_info = store.lookup_lls(data.location.postcode, data.location.suburb)
    if lls_info is None:
        raise HTTPException(404, f"No LLS mapping found for suburb '{data.location.suburb}'")

    stats = store.lookup_crop_stats(lls_info["region_id"], data.cropCategory)
    if stats is None or stats["n"] < 1:
        raise HTTPException(422, "Insufficient benchmark data for this LLS/crop combination.")

    z = compute_z_score(user_ml_per_ha, stats["mean"], stats["std"])
    risk_level = bucket_risk(z)

    risk = RiskResult(
        z_score=z, risk_level=risk_level, user_ml_per_ha=user_ml_per_ha,
        benchmark_mean=stats["mean"], benchmark_std=stats["std"], sample_size=stats["n"],
        lls_region=lls_info["region_id"], valley_name=lls_info["valley_name"],
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
    )