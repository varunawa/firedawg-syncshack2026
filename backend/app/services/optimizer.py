"""
Strategy-selection optimizer using scipy.optimize.milp (0/1 knapsack as a MILP).
See previous message for full rationale on the two optimization modes.
"""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from app.services.strategy_loader import ScaledStrategy


@dataclass
class OptimizationResult:
    success: bool
    message: str
    selected: list[ScaledStrategy]
    total_cost_aud: float
    total_savings_ml: float


def _empty_result(message: str) -> OptimizationResult:
    return OptimizationResult(success=False, message=message, selected=[],
                               total_cost_aud=0.0, total_savings_ml=0.0)


def select_optimal_strategies(
    candidates: list[ScaledStrategy],
    mode: str,
    budget_aud: float | None = None,
    target_savings_ml: float | None = None,
) -> OptimizationResult:
    if not candidates:
        return _empty_result("No applicable strategies for this farm/crop combination.")

    n = len(candidates)
    costs = np.array([c.annual_cost_aud for c in candidates])
    savings = np.array([c.savings_ml for c in candidates])

    integrality = np.ones(n)
    bounds = Bounds(lb=np.zeros(n), ub=np.ones(n))

    if mode == "maximize_savings_within_budget":
        if budget_aud is None:
            return _empty_result("budget_aud is required for maximize_savings_within_budget mode.")
        constraints = [LinearConstraint(costs, lb=-np.inf, ub=budget_aud)]
        c = -savings

    elif mode == "minimize_cost_to_target":
        if target_savings_ml is None:
            return _empty_result("target_savings_ml is required for minimize_cost_to_target mode.")
        if target_savings_ml <= 0:
            return _empty_result("target_savings_ml must be positive.")
        if savings.sum() < target_savings_ml:
            selected = list(candidates)
            return OptimizationResult(
                success=False,
                message=(f"Even adopting every applicable strategy only saves "
                          f"{savings.sum():.2f} ML/yr, short of the {target_savings_ml:.2f} ML/yr target."),
                selected=selected,
                total_cost_aud=float(costs.sum()),
                total_savings_ml=float(savings.sum()),
            )
        constraints = [LinearConstraint(savings, lb=target_savings_ml, ub=np.inf)]
        c = costs

    else:
        return _empty_result(f"Unknown optimization mode: {mode}")

    result = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)

    if not result.success:
        return _empty_result(f"Solver failed: {result.message}")

    selected_idx = np.where(result.x > 0.5)[0]
    selected = [candidates[i] for i in selected_idx]

    return OptimizationResult(
        success=True,
        message="optimal",
        selected=selected,
        total_cost_aud=float(sum(s.annual_cost_aud for s in selected)),
        total_savings_ml=float(sum(s.savings_ml for s in selected)),
    )