# Data dictionary — bmc-v1 (BMC Mumbai, converted 2026-10-05)

Keys: `ward_id` + `date` (`YYYY-MM-DD`). Water in ML. 1 MCM = 1000 ML.
Provenance: `WaterSphere_BMC_Mumbai_D1_D7/` via `scripts/convert_bmc_data.py`
(synthetic modelling assignment, ward-level estimates — NOT municipal SCADA;
treat as real-v1 stand-in, see limitations). Replaces synthetic-v1 (seed 42,
5 generic wards) entirely.

## data/raw/wards.csv
`ward_id, ward_name, area_km2` — 24 BMC wards (A, B, C, D, E, F/N, F/S, G/N,
G/S, H/E, H/W, K/E, K/W, L, M/E, M/W, N, P/N, P/S, R/C, R/N, R/S, S, T).

## data/raw/population.csv
`ward_id, ward_name, year, population, area_km2, density, growth_pct` —
ward×year 2023–2025 (72 rows + header = 73 lines). density = population/area_km2.

## data/raw/consumption.csv
`date, ward_id, demand_ml, water_supplied_ml, water_consumed_ml` — ward×daily
2023-01-01..2025-12-31 (24×1096=26304 rows). Source columns Demand_ML /
Water_Supplied_ML / Water_Consumed_ML carried over verbatim (implied LPCD
~240–250, loss ~10–11%). Zero duplicates, zero nulls (validate_data.py PASS).

## data/raw/reservoirs.csv
`reservoir_id, reservoir_name, lat, lon, capacity_mcm, serving_wards` — 7
sources: Bhatsa (976 MCM → A;G/S;M/E;R/N), Middle Vaitarna (202.1 → D;H/W;P/S),
Modak Sagar (128 → C;H/E;N;T), Tansa (80.9 → B;G/N;M/W;S), Tulsi (11 → F/N;L;R/C),
Upper Vaitarna (331 → E;K/E;P/N), Vihar (9.2 → F/S;K/W;R/S). Serving map is a
synthetic modelling assignment from the converter (see D1 Primary_Source note),
NOT an official BMC allocation. Coords from D5 approximate reference points.

## data/raw/reservoir_readings.csv
`reservoir_id, date, level_m, capacity_mcm, current_storage_mcm, storage_pct, available_water_ml`
— reservoir×daily (7×1096=7672 rows). storage_pct = current/capacity×100
(verified). available_water_ml carried from source. `level_m` is a PLACEHOLDER
(`storage_pct × 0.5`, converter line 104) — do not use for engineering claims.

## data/raw/maintenance.csv
`incident_id, date, ward_id, incident_type, cause, severity, resolved_date` —
123 non-Normal incidents converted from D6 (Normal rows = baseline loss, skipped).
IDs are converter-assigned (`INC_00001…`), not municipal ticket numbers.

## data/raw/wards.geojson
Centroid-box polygons (±0.02° around D5 ward centroids),
provenance=`bmc-mumbai-approximate-centroid`. Replace with authoritative BMC
boundary GeoJSON in Advanced (TODO P3).

## Source files NOT yet ingested
- D4 calendar: redundant (preprocess regenerates day/dow/month/season/weekend).
- D7 complaints + supply schedules: not loaded to DB; complaints API is manual
  CRUD only. Wiring D7 history in is an open improvement.
