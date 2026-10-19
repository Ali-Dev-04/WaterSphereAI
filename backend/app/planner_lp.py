"""LP supply allocator (Advanced, Phase 8 follow-up).

Same contract as the rule-based `planner.alloc`: split one reservoir pool
across served wards, never exceeding forecasts, using the full pool unless all
demands are met. Formulation (PuLP/CBC):

    max  Σ w_i · x_i        (severity-weighted met demand)
    s.t. 0 ≤ x_i ≤ f_i      (no ward exceeds forecast)
         Σ x_i ≤ pool        (never over-allocate)

With strictly positive weights the optimum exhausts the pool whenever total
demand exceeds it, and meets every forecast under surplus — matching the
rule-based guarantees, with provable optimality instead of heuristics.
Selected via env SUPPLY_OPTIMIZER=rule|lp (default rule).
"""

from __future__ import annotations

import pulp

from app.planner import SEVERITY_WEIGHT


def alloc_lp(pool: float, forecasts: list[float], ranks: list[int]) -> list[float]:
    """Pure function: LP-optimal split of pool across wards. Unit-tested without DB."""
    n = len(forecasts)
    if n == 0 or pool <= 0 or sum(forecasts) <= 0:
        return [0.0] * n
    prob = pulp.LpProblem("ward_supply", pulp.LpMaximize)
    xs = [pulp.LpVariable(f"x{i}", lowBound=0, upBound=max(f, 0.0)) for i, f in enumerate(forecasts)]
    prob += pulp.lpSum(SEVERITY_WEIGHT[r] * x for r, x in zip(ranks, xs))
    prob += pulp.lpSum(xs) <= pool
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[prob.status] != "Optimal":
        raise RuntimeError(f"LP allocation failed: {pulp.LpStatus[prob.status]}")
    return [round(min(max(float(pulp.value(x) or 0.0), 0.0), f), 4)
            for x, f in zip(xs, forecasts)]
