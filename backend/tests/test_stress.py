"""Unit tests for stress logic: worked example, boundaries, zero-guard."""

from app import stress
from app.config import settings


def test_worked_example():
    # PDF §14/§15: 500 ML forecast, 450 ML available → gap 50, WAR 0.90.
    forecast, available = 500.0, 450.0
    assert round(forecast - available, 4) == 50.0
    assert round(available / forecast, 4) == 0.9
    assert stress.classify(0.9) == "Moderate"


def test_threshold_boundaries():
    assert stress.classify(settings.war_safe) == "Safe"
    assert stress.classify(settings.war_moderate) == "Moderate"
    assert stress.classify(settings.war_high) == "High Stress"
    assert stress.classify(settings.war_high - 0.001) == "Shortage"
    assert stress.classify(1.5) == "Safe"
    assert stress.classify(0.0) == "Shortage"


def test_thresholds_adjustable_without_code_change(monkeypatch):
    monkeypatch.setattr(settings, "war_moderate", 0.95)
    assert stress.classify(0.9) == "High Stress"  # was Moderate under defaults
