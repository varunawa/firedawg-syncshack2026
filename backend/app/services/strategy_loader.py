import json
from dataclasses import dataclass
from functools import lru_cache

from app.config import settings


@dataclass
class ScaledStrategy:
    id: str
    name: str
    category: str
    annual_cost_aud: float
    savings_ml: float
    savings_pct_applied: float
    implementation_disruption: str
    confidence: str
    source: str


class StrategyCatalog:
    def __init__(self):
        if not settings.strategy_catalog_path.exists():
            self._raw = []
            return
        with open(settings.strategy_catalog_path) as f:
            payload = json.load(f)
        self._raw = payload.get("strategies", [])

    def applicable_strategies(self, crop_category: str, current_irrigation: str) -> list[dict]:
        out = []
        for s in self._raw:
            crops = s["applicable_crop_categories"]
            if crops != "ALL" and crop_category not in crops:
                continue
            if current_irrigation in s.get("not_applicable_if_current_irrigation", []):
                continue
            out.append(s)
        return out

    def scale_to_farm(self, strategy: dict, user_ml_per_ha: float, land_area_ha: float) -> ScaledStrategy:
        cm = strategy["cost_model"]
        area_fraction = cm.get("capped_area_fraction", 1.0)

        capital = cm.get("fixed_aud", 0) + cm.get("per_ha_aud", 0) * land_area_ha * area_fraction
        lifespan = strategy.get("lifespan_years", 1) or 1

        annual_capital = capital / lifespan
        annual_maintenance = capital * strategy.get("annual_maintenance_pct", 0.0)
        annual_recurring = cm.get("recurring_annual_aud", 0) + cm.get("flat_annual_service_aud", 0)

        annual_cost = annual_capital + annual_maintenance + annual_recurring

        effective_savings_pct = strategy["savings_pct_default"] * area_fraction
        savings_ml = user_ml_per_ha * land_area_ha * effective_savings_pct

        return ScaledStrategy(
            id=strategy["id"],
            name=strategy["name"],
            category=strategy["category"],
            annual_cost_aud=round(annual_cost, 2),
            savings_ml=round(savings_ml, 3),
            savings_pct_applied=effective_savings_pct,
            implementation_disruption=strategy["implementation_disruption"],
            confidence=strategy["confidence"],
            source=strategy["source"],
        )

    def candidates_for_farm(self, crop_category: str, current_irrigation: str,
                             user_ml_per_ha: float, land_area_ha: float) -> list[ScaledStrategy]:
        applicable = self.applicable_strategies(crop_category, current_irrigation)
        return [self.scale_to_farm(s, user_ml_per_ha, land_area_ha) for s in applicable]


@lru_cache(maxsize=1)
def get_strategy_catalog() -> StrategyCatalog:
    return StrategyCatalog()