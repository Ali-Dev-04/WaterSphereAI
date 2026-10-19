# Quality report — Phase 2 (bmc-v1)

- merged rows: 26304 (wards 24 x dates 1096)
- period: 2023-01-01..2025-12-31
- duplicates removed: consumption=0, readings=0
- missing % before: {'consumption': 0.0, 'population': 0.0, 'reservoirs': 0.0, 'readings': 0.0, 'wards': 0.0}
- missing % after impute: {'consumption': 0.0, 'population': 0.0, 'reservoirs': 0.0, 'readings': 0.0, 'wards': 0.0}
- outliers capped (IQR per ward): {'demand_ml': 453, 'water_consumed_ml': 381}
- reservoir mapping: equal split among served wards (per reservoirs.csv serving_wards; 7 BMC reservoirs)
- scaling: deferred to Phase 3 (fit on train only, no leakage)
- assertions: 1:1 ward-date merge, no null keys, row count == ward x date — all PASS
