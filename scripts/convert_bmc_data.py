"""Convert WaterSphere_BMC_Mumbai_D1_D7 dataset into data/raw/ contract format."""

import csv
import json
import os
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "WaterSphere_BMC_Mumbai_D1_D7"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    # 1. Wards & Population
    with open(SRC / "D1_BMC_population.csv") as f:
        r = list(csv.DictReader(f))

    wards_dict = {}
    pop_rows = []
    for row in r:
        wid = row["Ward_ID"]
        name = row["Ward_Name"]
        area = float(row["Area_km2"])
        pop = int(row["Population"])
        density = round(pop / area, 4)

        if wid not in wards_dict:
            wards_dict[wid] = {"ward_id": wid, "ward_name": name, "area_km2": area}

        pop_rows.append({
            "ward_id": wid,
            "ward_name": name,
            "year": int(row["Year"]),
            "population": pop,
            "area_km2": area,
            "density": density,
            "growth_pct": float(row["Growth_%"])
        })

    with open(RAW / "wards.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ward_id", "ward_name", "area_km2"])
        w.writeheader()
        for wid in sorted(wards_dict.keys()):
            w.writerow(wards_dict[wid])

    with open(RAW / "population.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ward_id", "ward_name", "year", "population", "area_km2", "density", "growth_pct"])
        w.writeheader()
        w.writerows(pop_rows)

    # 2. Consumption
    with open(SRC / "D2_BMC_consumption_supply.csv") as f:
        r = list(csv.DictReader(f))

    c_rows = []
    for row in r:
        c_rows.append({
            "date": row["Date"],
            "ward_id": row["Ward_ID"],
            "demand_ml": float(row["Demand_ML"]),
            "water_supplied_ml": float(row["Water_Supplied_ML"]),
            "water_consumed_ml": float(row["Water_Consumed_ML"])
        })

    with open(RAW / "consumption.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "ward_id", "demand_ml", "water_supplied_ml", "water_consumed_ml"])
        w.writeheader()
        w.writerows(c_rows)

    # 3. Reservoirs & Reservoir Readings
    res_wards_map = {
        "Bhatsa": "A;G/S;M/E;R/N",
        "Middle Vaitarna": "D;H/W;P/S",
        "Modak Sagar": "C;H/E;N;T",
        "Tansa": "B;G/N;M/W;S",
        "Tulsi": "F/N;L;R/C",
        "Upper Vaitarna": "E;K/E;P/N",
        "Vihar": "F/S;K/W;R/S"
    }

    res_coords = {}
    ward_coords = {}
    with open(SRC / "D5_BMC_GIS_locations.csv") as f:
        for row in csv.DictReader(f):
            if row["Feature_Type"] == "RESERVOIR":
                res_coords[row["Feature_ID"]] = (float(row["Lat"]), float(row["Lon"]))
            elif row["Feature_Type"] == "WARD":
                ward_coords[row["Feature_ID"]] = (float(row["Lat"]), float(row["Lon"]))

    with open(SRC / "D3_BMC_reservoir_sources.csv") as f:
        r = list(csv.DictReader(f))

    res_master = {}
    readings = []
    for row in r:
        rid = row["Reservoir_ID"]
        cap_ml = float(row["Capacity_ML"])
        cap_mcm = cap_ml / 1000.0
        curr_ml = float(row["Current_Storage_ML"])
        curr_mcm = curr_ml / 1000.0
        storage_pct = round(curr_mcm / cap_mcm * 100.0, 4)
        available_ml = float(row["Available_Water_ML"])
        level_m = round(storage_pct * 0.5, 2)

        if rid not in res_master:
            lat, lon = res_coords.get(rid, (19.5, 73.0))
            res_master[rid] = {
                "reservoir_id": rid,
                "reservoir_name": rid,
                "lat": lat,
                "lon": lon,
                "capacity_mcm": round(cap_mcm, 2),
                "serving_wards": res_wards_map.get(rid, "")
            }

        readings.append({
            "reservoir_id": rid,
            "date": row["Date"],
            "level_m": level_m,
            "capacity_mcm": round(cap_mcm, 4),
            "current_storage_mcm": round(curr_mcm, 4),
            "storage_pct": storage_pct,
            "available_water_ml": available_ml
        })

    with open(RAW / "reservoirs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["reservoir_id", "reservoir_name", "lat", "lon", "capacity_mcm", "serving_wards"])
        w.writeheader()
        for rid in sorted(res_master.keys()):
            w.writerow(res_master[rid])

    with open(RAW / "reservoir_readings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["reservoir_id", "date", "level_m", "capacity_mcm", "current_storage_mcm", "storage_pct", "available_water_ml"])
        w.writeheader()
        w.writerows(readings)

    # 4. Maintenance / Leakage
    with open(SRC / "D6_BMC_leakage_maintenance.csv") as f:
        r = list(csv.DictReader(f))

    maint_rows = []
    inc_idx = 1
    for row in r:
        if row["Incident_Type"] != "Normal":
            maint_rows.append({
                "incident_id": f"INC_{inc_idx:05d}",
                "date": row["Date"],
                "ward_id": row["Ward_ID"],
                "incident_type": row["Incident_Type"],
                "cause": row["Cause"],
                "severity": row["Severity"],
                "resolved_date": row["Resolved_Date"] if row["Resolved_Date"] else row["Date"]
            })
            inc_idx += 1

    with open(RAW / "maintenance.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["incident_id", "date", "ward_id", "incident_type", "cause", "severity", "resolved_date"])
        w.writeheader()
        w.writerows(maint_rows)

    # 5. GeoJSON
    features = []
    delta = 0.02
    for wid in sorted(ward_coords.keys()):
        lat, lon = ward_coords[wid]
        poly = [
            [round(lon - delta, 4), round(lat - delta, 4)],
            [round(lon + delta, 4), round(lat - delta, 4)],
            [round(lon + delta, 4), round(lat + delta, 4)],
            [round(lon - delta, 4), round(lat + delta, 4)],
            [round(lon - delta, 4), round(lat - delta, 4)],
        ]
        features.append({
            "type": "Feature",
            "properties": {
                "ward_id": wid,
                "provenance": "bmc-mumbai-approximate-centroid"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly]
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(RAW / "wards.geojson", "w") as f:
        json.dump(geojson, f, indent=2)

    print("Conversion complete!")
    print(f"Wards: {len(wards_dict)}")
    print(f"Population rows: {len(pop_rows)}")
    print(f"Consumption rows: {len(c_rows)}")
    print(f"Reservoirs: {len(res_master)}")
    print(f"Readings: {len(readings)}")
    print(f"Maintenance incidents: {len(maint_rows)}")
    print(f"GeoJSON features: {len(features)}")


if __name__ == "__main__":
    main()
