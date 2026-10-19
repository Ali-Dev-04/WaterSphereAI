"""Unit tests for the allocator: conservation, caps, priority, reserve, alerts."""

from app.planner import ALERT_CATEGORIES, SEVERITY_RANK, alloc


def test_allocates_full_pool_when_demand_exceeds():
    got = alloc(100.0, [60.0, 60.0, 60.0], [3, 3, 3])
    assert abs(sum(got) - 100.0) < 1e-6
    assert all(g <= 60.0 + 1e-9 for g in got)


def test_never_exceeds_forecast_surplus_stays_stored():
    got = alloc(100.0, [10.0, 20.0], [0, 0])
    assert got == [10.0, 20.0]
    assert sum(got) == 30.0  # surplus 70 stays in reservoir


def test_higher_severity_gets_more():
    # Scarcity: pool 60 < demand 100 → weights 4:1 → Shortage 48, Safe 12.
    got = alloc(60.0, [50.0, 50.0], [SEVERITY_RANK["Shortage"], SEVERITY_RANK["Safe"]])
    assert got[0] == 48.0 and got[1] == 12.0
    assert abs(sum(got) - 60.0) < 1e-6


def test_alert_categories():
    assert "High Stress" in ALERT_CATEGORIES and "Shortage" in ALERT_CATEGORIES
    assert "Safe" not in ALERT_CATEGORIES and "Moderate" not in ALERT_CATEGORIES


def test_empty_or_zero_pool():
    assert alloc(0.0, [50.0], [0]) == [0.0]
    assert alloc(100.0, [0.0, 0.0], [0, 0]) == [0.0, 0.0]
