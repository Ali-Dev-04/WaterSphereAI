import pandas as pd

m = pd.read_csv("data/processed/merged_ward_date.csv", parse_dates=["date"])
m["war_proxy"] = m["available_water_ml"] / m["demand_ml"]
m["shortfall"] = (m["water_supplied_ml"] - m["demand_ml"]) / m["demand_ml"]
print("WAR proxy quantiles:")
print(m["war_proxy"].quantile([0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).round(3).to_dict())
print("shortfall quantiles:")
print(m["shortfall"].quantile([0.01, 0.05, 0.1, 0.25, 0.5]).round(4).to_dict())
print("ward-days supply shortfall>5%:", int((m["shortfall"] < -0.05).sum()), "/", len(m))
for b in (0.70, 0.85, 1.0):
    print(f"ward-days WAR<{b}:", int((m["war_proxy"] < b).sum()))
print("median WAR on shortfall>5% days:", round(m.loc[m["shortfall"] < -0.05, "war_proxy"].median(), 3))
print("median WAR on normal days:", round(m.loc[m["shortfall"] >= -0.05, "war_proxy"].median(), 3))

# Canonical worked example (PRD FR5 / Architecture §5): 500 forecast, 450 available.
gap, war = 500 - 450, 450 / 500
band = "Safe" if war >= 1.0 else "Moderate" if war >= 0.85 else "High Stress" if war >= 0.70 else "Shortage"
assert (gap, round(war, 2), band) == (50, 0.90, "Moderate"), "canonical WAR example broken"
print(f"canonical check PASS: gap={gap}, WAR={war:.2f} → {band}")
print("live-API check: expect all-Safe on BMC window (min ward WAR≈2.9, no absolute scarcity).")
