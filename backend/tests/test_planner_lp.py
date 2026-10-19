"""Unit tests for the LP allocator: same contract as rule-based alloc."""

import pytest

from app.planner import SEVERITY_RANK
from app.planner_lp import alloc_lp

pulp = pytest.importorskip("pulp")


def test_lp_allocates_full_pool_when_demand_exceeds():
    got = alloc_lp(100.0, [60.0, 60.0, 60.0], [3, 3, 3])
    assert abs(sum(got) - 100.0) < 1e-3
    assert all(g <= 60.0 + 1e-6 for g in got)


def test_lp_never_exceeds_forecast_surplus_stays_stored():
    got = alloc_lp(100.0, [10.0, 20.0], [0, 0])
    assert got == [10.0, 20.0]
    assert sum(got) == 30.0


def test_lp_higher_severity_gets_more():
    # Scarcity: pool 60 < demand 100 → all 60 go to the Shortage ward first.
    got = alloc_lp(60.0, [50.0, 50.0], [SEVERITY_RANK["Shortage"], SEVERITY_RANK["Safe"]])
    assert got[0] == 50.0 and got[1] == 10.0
    assert abs(sum(got) - 60.0) < 1e-3


def test_lp_empty_or_zero_pool():
    assert alloc_lp(0.0, [50.0], [0]) == [0.0]
    assert alloc_lp(100.0, [0.0, 0.0], [0, 0]) == [0.0, 0.0]


def test_lp_agrees_with_rule_based_under_surplus():
    from app.planner import alloc
    fc, ranks = [48.1, 33.4, 90.7], [3, 2, 1]
    assert alloc_lp(1000.0, fc, ranks) == alloc(1000.0, fc, ranks) == fc
