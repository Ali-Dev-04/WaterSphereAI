"""Unit tests for leakage module: loss math, spike detection, determinism."""

import datetime as dt

from app.leakage import flag_anomalies, loss_frame


def _series(n=60, spike_day=None):
    dates = [dt.date(2025, 1, 1) + dt.timedelta(days=i) for i in range(n)]
    supplied = [10.0] * n
    consumed = [9.0] * n
    if spike_day is not None:
        consumed[spike_day] = 4.0  # 6 ML loss vs ~1 ML baseline
    return loss_frame(dates, supplied, consumed)


def test_loss_formula():
    df = _series()
    assert (df.loss_ml == 1.0).all()
    assert abs(df.loss_pct.iloc[0] - 0.1) < 1e-9


def test_spike_gets_flagged():
    df = flag_anomalies(_series(spike_day=30))
    flagged = df[df.flag]
    assert "2025-01-31" in set(flagged.date.dt.strftime("%Y-%m-%d"))
    row = df[df.date == "2025-01-31"].iloc[0]
    assert row.severity == "high"


def test_deterministic():
    a = flag_anomalies(_series(spike_day=10))
    b = flag_anomalies(_series(spike_day=10))
    assert list(a.flag) == list(b.flag)
    assert list(a.score) == list(b.score)
