# data.md — Core & Supporting Datasets for WaterSphere AI

Source: derived from `Docs/IMPLEMENTATION_PLAN.md §1.11, Phase 1–3` + Development Context PDF `§4,6,17,20,22,28`. Stage 0: no dataset exists yet — this file defines what to collect/keep handy.

## 0. Global Keys & Conventions
- Join key everywhere: `Ward_ID + Date` (`Date` = ISO `YYYY-MM-DD`).
- Units: water in **ML** (or MCM with conversion noted); population absolute; density per km².
- Keep raw (immutable) + clean (processed) copies separately. Never overwrite raw.
- Every file ships with a provenance line: source, URL/access date, license, grain, coverage.

## 1. Core Datasets (block Phase 1–5 if missing)

### D1 — Population, ward-level
**Fields:** `Ward_ID, Ward_Name, Year, Population, Area_km2, Density, Growth_%`
**Grain/volume:** ward × year, minimum 3–5 years to capture growth trend.
**Keep handy as:** `population.csv` + ward master `wards.csv (Ward_ID, Ward_Name, Area_km2)`.
**Sources:**
1. Census of India 2011 + projections — `data.censusindia.gov.in`
2. Target Municipal Corporation ward handbook / Smart City DPR / water-board planning reports (e.g. BWSSB, DJB, BMC, CMWSSB, HMWSSB depending on chosen city)
3. `data.gov.in` — search `ward population`
**Acceptance:** every `Ward_ID` in D2 exists in D1; density = pop/area recomputes.

### D2 — Historical water consumption / supply (training target)
**Fields:** `Date, Ward_ID, Water_Consumed_ML, Water_Supplied_ML, Demand_ML`
**Grain/volume:** **daily, ≥1–2 years** — required for 7-day horizon + 30-day rolling features (Phase 3). This is the model label (`Actual Demand`).
**Keep handy as:** `consumption.csv`, sorted by `Ward_ID, Date`, no duplicate ward-dates.
**Sources:**
1. Municipal water-board daily supply logs / SCADA bulletins — typically only via direct request/RTI; most public portals publish city-level monthly only (insufficient — verify grain before committing).
2. Prototype fallback: Kaggle `water consumption / demand forecasting` datasets (label provenance as proxy).
3. Synthetic fallback (allowed as labeled PoC): generate from D1 × CPHEEO norm ~135 lpcd × seasonal curve (summer peak) + noise; clearly flag `provenance=synthetic`.
**Acceptance:** continuous daily coverage per ward; missing % documented; `Loss = Supplied − Consumed` computable for D6.

### D3 — Reservoir availability (resource side)
**Fields:** `Reservoir_ID, Reservoir_Name, Lat, Lon, Date, Level_m, Total_Capacity_MCM, Current_Storage_MCM, Storage_%, Available_Water_ML, Serving_Wards[]`
**Grain/volume:** daily/weekly matching D2 period. Formulas: `Storage% = Current/Capacity×100`.
**Keep handy as:** `reservoirs.csv` + `reservoir_readings.csv`.
**Sources:**
1. Central Water Commission — `cwc.gov.in` weekly live-storage bulletins
2. India-WRIS — `indiawris.gov.in`
3. State dam circle / municipal reservoir inflow registers (for serving-ward mapping + lat/lon)
**Acceptance:** readings joinable to forecast dates; worked example reproduces (450 ML available).

### D4 — Time / Season calendar (derived, no collection)
**Fields:** `Date, Day, DayOfWeek, Month, Year, Season, Weekend_Flag`
**Keep handy as:** generated in code from D2/D3 `Date` (pandas). No external source.
**Note:** festival/holiday flag optional later; rainfall/weather explicitly out of scope — do not collect.

## 2. Supporting Datasets (need for Phase 7, 10, 11, 12)

### D5 — Ward boundaries + reservoir locations (GIS, Phase 10)
**Fields:** `Ward_ID → GeoJSON Polygon; Reservoir_ID → Point(lat, lon)`
**Keep handy as:** `wards.geojson`, `reservoirs.geojson` (keys must match D1/D3 IDs).
**Sources:** municipal GIS/town-planning cell; ISRO Bhuvan (`bhuvan.nrsc.gov.in`); OSM Overpass as fallback. MVP fallback: simplified grid polygons labeled `approximate`.
**Acceptance:** every `Ward_ID` renders; stress choropleth colors per `Design_System.md`.

### D6 — Leakage / wastage / maintenance (Phase 12, supporting)
**Fields:** computed `Water Loss = Supplied − Consumed` (from D2, free). Supervised-only fields if available: `Date, Ward_ID, Location, Incident_Type (burst/leak/valve), Cause, Severity, Resolved_Date`.
**Sources:** municipal line-burst / complaint registers, maintenance logbooks. Often unavailable → default to unsupervised `IsolationForest` on supply/consumption patterns (no labels needed).
**Keep handy as:** `maintenance.csv` (even 50–100 rows of seed incidents help testing).

### D7 — Complaints + supply-schedule seeds (Phase 11/12 testing)
**Fields:** `Complaint_ID, User_ID, Ward_ID, Type, Status (Filed/In-progress/Resolved), Created_At, Updated_At`; `Ward_ID, Scheduled_Supply_Time, Supply_Days`
**Sources:** generated in-app; keep 20–50 sample rows + type taxonomy (`no-supply, low-pressure, leakage, quality, billing`) in `tests/fixtures/`.
**Acceptance:** citizen journey testable E2E without manual DB edits.

## 3. Explicitly NOT Needed for MVP
Rainfall/weather, water-quality lab data, LP/MILP solver data, multi-city feeds — Future scope only.

## 4. Handy File Layout (proposed)
```
data/
  raw/{population.csv, consumption.csv, reservoirs.csv, reservoir_readings.csv,
       wards.geojson, maintenance.csv}
  processed/{merged_ward_date.csv, features.csv, train.csv, val.csv, test.csv}
  data_dictionary.md   # field defs + units + grain per table above
  provenance.txt       # source, URL, access date, license per file
```

## 5. Collection Priority
1. Fix municipality first (unblocks everything). 2. Pull D1 + D3 (easiest, most public). 3. Feasibility-spike D2 grain check (ward-daily vs city-monthly?). 4. If D2 fails → approve synthetic D2/D3 and proceed; pipeline stays source-agnostic so real data swaps in later.
