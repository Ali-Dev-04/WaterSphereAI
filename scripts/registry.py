"""Model registry snapshot: versioned manifest of the production model set.

Regenerates models/manifest.json from validation/test metrics + data state.
Run after every retrain before re-seeding or deploying. No retraining here.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha_short(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def main() -> None:
    valm = json.loads((ROOT / "data" / "validation_metrics.json").read_text())
    testm = json.loads((ROOT / "data" / "test_metrics.json").read_text())
    active = json.loads((ROOT / "models" / "active.json").read_text())
    prov = (ROOT / "data" / "provenance.txt").read_text().strip().splitlines()[0]
    split = json.loads((ROOT / "data" / "processed" / "split_meta.json").read_text())
    manifest = {
        "model_version": "bmc-v1",
        "data_version": prov,
        "snapshot_date": str(date.today()),
        "selection_rule": active["selected_on"],
        "active_per_horizon": active["best_per_horizon"],
        "artifacts": {},
        "metrics": {"validation": valm, "test": testm},
        "splits": {k: split[k] for k in ("cut1", "cut2", "train", "val", "test")},
        "notes": [
            "xgb_*.pkl are sklearn HistGradientBoostingRegressor (libomp missing on host); API-compatible.",
            "Retraining policy: monthly scheduled + MAPE-guard trigger (see EVALUATION.md §7).",
        ],
    }
    for h, fam in active["best_per_horizon"].items():
        p = ROOT / "models" / (f"xgb_{h}.pkl" if fam == "xgboost" else f"{fam}_{h}.keras")
        manifest["artifacts"][h] = {"family": fam, "file": p.name, "sha12": sha_short(p)}
    (ROOT / "models" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("manifest ok:", manifest["active_per_horizon"], "snapshot", manifest["snapshot_date"])


if __name__ == "__main__":
    main()
