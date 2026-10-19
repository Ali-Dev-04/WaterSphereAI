"""Phase 13 (integration/E2E) + Phase 14 (live security) verification.

Runs against the live stack from the outside, like the deployed dashboard would.
Exit 0 = all checks pass. Rate-limit probe runs LAST (it exhausts the login budget).
Stdlib only.

Updated 2026-10-05: BMC Mumbai 24-ward dataset (bmc-v1). Ward IDs are now
single/double-letter codes (A, B, C, ... T, F/N, F/S, etc.). Citizen user
is ward A. Reservoirs: Bhatsa, Tansa, Modak Sagar, Upper Vaitarna,
Middle Vaitarna, Vihar, Tulsi.
"""

import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:8000"
FAILURES: list[str] = []

# BMC ward/reservoir constants
WARD_A = "A"     # citizen_w1's ward
WARD_B = "B"     # another ward for cross-ward 403 test
RESERVOIR_1 = "Bhatsa"
TEST_DATE = "2025-12-20"
N_WARDS = 24


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def call(method: str, path: str, token: str | None = None, body: dict | None = None,
         query: dict | None = None) -> tuple[int, object]:
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "null")
        except Exception:
            return e.code, None


def login(username: str, password: str) -> str:
    code, body = call("POST", "/api/auth/login",
                      body={"username": username, "password": password})
    check(f"login {username}", code == 200, f"got {code}")
    return body["access_token"]


def main() -> None:
    # ---------- J1: admin full pipeline ----------
    admin = login("admin", "admin123")
    code, wards = call("GET", "/api/wards", admin)
    check(f"wards = {N_WARDS}", code == 200 and len(wards) == N_WARDS, f"got {code}/{len(wards) if isinstance(wards, list) else wards!r}")
    fc = {}
    for h in ("1d", "3d", "7d"):
        code, body = call("GET", "/api/forecast", admin,
                          query={"ward_id": WARD_A, "target_date": TEST_DATE, "horizon": h})
        check(f"forecast {h} live", code == 200 and body["predicted_ml"] > 0, f"got {code}")
        fc[h] = body
    check("active models served", fc["1d"]["model"] == "xgboost" and fc["3d"]["model"] == "gru" and fc["7d"]["model"] == "gru",
          str({h: fc[h]["model"] for h in fc}))
    code, st = call("GET", "/api/water-stress", admin,
                    query={"ward_id": WARD_A, "date": TEST_DATE})
    ok = (code == 200 and abs(st["gap_ml"] - (st["forecast_ml"] - st["available_ml"])) < 1e-3
          and abs(st["war"] - st["available_ml"] / st["forecast_ml"]) < 1e-3
          and abs(st["forecast_ml"] - fc["1d"]["predicted_ml"]) < 1e-9)
    check("stress math consistent w/ forecast", ok, str(st)[:120])
    code, plan = call("GET", "/api/supply-plan", admin, query={"date": TEST_DATE})
    alloc_by_res: dict[str, float] = {}
    fore_by_ward = {w["ward_id"]: w["forecast_ml"] for w in plan["wards"]}
    ok = code == 200
    for w in plan["wards"]:
        alloc_by_res[w["reservoir_id"]] = alloc_by_res.get(w["reservoir_id"], 0) + w["allocated_ml"]
        ok = ok and w["allocated_ml"] <= fore_by_ward[w["ward_id"]] + 1e-6
        if w["category"] in ("High Stress", "Shortage"):
            ok = ok and w["alert"] is True
    for p in plan["pools"]:
        ok = ok and alloc_by_res.get(p["reservoir_id"], 0) <= p["pool_ml"] + 1e-3
    check("plan conserves pools, caps demands, alerts", ok)

    # ---------- J2/J3: citizen journey + complaint round-trip ----------
    cit = login("citizen_w1", "citizen123")
    code, _ = call("GET", "/api/forecast", cit,
                   query={"ward_id": WARD_A, "target_date": TEST_DATE, "horizon": "1d"})
    check("citizen own forecast 200", code == 200, f"got {code}")
    code, _ = call("GET", "/api/forecast", cit,
                   query={"ward_id": WARD_B, "target_date": TEST_DATE, "horizon": "1d"})
    check("citizen cross-ward 403", code == 403, f"got {code}")
    code, mine = call("GET", "/api/supply-plan", cit, query={"date": TEST_DATE})
    check("citizen plan scoped to own ward",
          code == 200 and [w["ward_id"] for w in mine["wards"]] == [WARD_A], f"got {code}")
    code, comp = call("POST", "/api/complaints", cit,
                      body={"ward_id": WARD_A, "type": "e2e-probe"})
    check("citizen files complaint", code == 201 and comp["status"] == "Filed", f"got {code}")
    cid = comp["id"]
    code, _ = call("PATCH", f"/api/complaints/{cid}", cit, body={"status": "Resolved"})
    check("citizen patch forbidden", code == 403, f"got {code}")
    code, allc = call("GET", "/api/complaints", admin)
    check("admin sees complaint", code == 200 and any(c["id"] == cid for c in allc),
          f"got {code}")
    code, upd = call("PATCH", f"/api/complaints/{cid}", admin, body={"status": "Resolved"})
    check("admin resolves", code == 200 and upd["status"] == "Resolved", f"got {code}")
    code, mine2 = call("GET", "/api/complaints", cit)
    check("citizen sees resolution",
          code == 200 and any(c["id"] == cid and c["status"] == "Resolved" for c in mine2),
          f"got {code}")

    # ---------- J4: supporting endpoints ----------
    for path, q in [("/api/leakage-risk", {"ward_id": WARD_A, "date_from": "2025-11-01", "date_to": TEST_DATE}),
                    ("/api/gis", {"date": TEST_DATE}),
                    ("/api/maintenance", {"ward_id": WARD_A}),
                    ("/api/reservoir", {"reservoir_id": RESERVOIR_1}),
                    ("/openapi.json", None)]:
        code, body = call("GET", path, admin, query=q)
        check(f"GET {path} 200", code == 200, f"got {code}")
    code, _ = call("GET", "/api/consumption", None,
                   query={"ward_id": WARD_A})
    check("no-token 401", code == 401, f"got {code}")

    # ---------- S: security live checks ----------
    code, _ = call("POST", "/api/auth/login", body={"username": "admin", "password": "wrong"})
    check("wrong password 401", code == 401, f"got {code}")
    code, _ = call("POST", "/api/auth/login", body={"username": "nosuch", "password": "x"})
    check("unknown user 401", code == 401, f"got {code}")
    code, _ = call("GET", "/api/wards", "tampered.token.here")
    check("tampered token 401", code == 401, f"got {code}")
    code, _ = call("POST", "/api/auth/register",
                   body={"username": "mallory", "password": "password1", "role": "admin", "ward_id": WARD_A})
    check("self-register admin blocked 403", code == 403, f"got {code}")
    code, _ = call("POST", "/api/auth/register",
                   body={"username": "admin", "password": "password1", "role": "citizen", "ward_id": WARD_A})
    check("duplicate username 409", code == 409, f"got {code}")
    code, _ = call("GET", "/api/forecast", admin,
                   query={"ward_id": "ZZZ", "target_date": TEST_DATE, "horizon": "1d"})
    check("unknown ward 404", code == 404, f"got {code}")
    payload = json.loads(base64.urlsafe_b64decode(admin.split(".")[1] + "=="))
    skew_min = (payload["exp"] - int(time.time())) / 60
    check("JWT expiry ≈60min", 50 < skew_min <= 61, f"{skew_min:.1f}min")

    # ---------- rate limit LAST ----------
    codes = [call("POST", "/api/auth/login",
                  body={"username": "admin", "password": "wrong"})[0] for _ in range(11)]
    check("login rate-limited (≥1× 429)", 429 in codes, str(sorted(set(codes))))

    print(f"\n{len(FAILURES)} failures" if FAILURES else "\nALL CHECKS PASSED")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
