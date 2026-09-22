"""
Generate tiny synthetic CSV samples for all three domains so the walkthrough can
run out of the box. Deterministic (seeded) so re-runs are stable.

Run from the repo root:

    python data/samples/generate_synthetic.py
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent  # data/samples/
SEED = 42


def _ee_samples() -> None:
    rng = random.Random(SEED)
    out = ROOT / "equitable_earth"
    out.mkdir(exist_ok=True)

    parcels = [f"P{i:02d}" for i in range(1, 6)]
    dates = [datetime(2026, 6, 1) + timedelta(days=7 * k) for k in range(6)]

    ndvi = [
        {
            "parcel_id": p,
            "date": d,
            "ndvi_mean": round(0.55 + rng.uniform(-0.15, 0.15), 3),
            "ndvi_stddev": round(rng.uniform(0.02, 0.08), 3),
        }
        for p in parcels
        for d in dates
    ]
    pd.DataFrame(ndvi).to_csv(out / "sentinel2_ndvi.csv", index=False)

    ground = [
        {
            "parcel_id": p,
            "date": d,
            "plot_biomass": round(15 + rng.uniform(-3, 3), 2),
            "plot_stddev": round(rng.uniform(0.5, 1.5), 2),
        }
        for p in parcels
        for d in dates[::2]  # sparser ground truth — matches reality
    ]
    pd.DataFrame(ground).to_csv(out / "ground_plots.csv", index=False)

    declared = [
        {
            "parcel_id": p,
            "date": dates[0],
            "declared_biomass": round(18 + rng.uniform(0, 4), 2),  # slightly optimistic bias
        }
        for p in parcels
    ]
    pd.DataFrame(declared).to_csv(out / "declared.csv", index=False)


def _kayrros_samples() -> None:
    """Kayrros forest-carbon synthetic data — S2 optical + S1 SAR + declared baseline.

    Values are on the same illustrative biomass scale (t/ha) so the pipeline can
    combine them directly. Real pipeline replaces these CSVs with STAC + zonal-stats
    outputs — see adapters/kayrros.py for the plan.
    """
    rng = random.Random(SEED + 1)
    out = ROOT / "kayrros"
    out.mkdir(exist_ok=True)

    assets = [f"A{i:02d}" for i in range(1, 6)]
    dates = [datetime(2026, 6, 1) + timedelta(days=7 * k) for k in range(6)]

    ndvi = [
        {
            "asset_id": a,
            "date": d,
            "ndvi_mean": round(0.55 + rng.uniform(-0.15, 0.15), 3),
            "ndvi_stddev": round(rng.uniform(0.02, 0.08), 3),
        }
        for a in assets
        for d in dates
    ]
    pd.DataFrame(ndvi).to_csv(out / "sentinel2_ndvi.csv", index=False)

    # SAR biomass proxy — deliberately biased slightly different from NDVI to make
    # disagreement visible (which is the whole point of the pipeline).
    sar = [
        {
            "asset_id": a,
            "date": d,
            "sar_biomass": round(16 + rng.uniform(-4, 4), 2),
            "sar_stddev": round(rng.uniform(0.8, 2.0), 2),
        }
        for a in assets
        for d in dates
    ]
    pd.DataFrame(sar).to_csv(out / "sentinel1_sar.csv", index=False)

    declared = [
        {
            "asset_id": a,
            "date": dates[0],
            "declared_stock": round(19 + rng.uniform(0, 4), 2),  # self-report optimism
        }
        for a in assets
    ]
    pd.DataFrame(declared).to_csv(out / "declared.csv", index=False)


def _ubees_samples() -> None:
    rng = random.Random(SEED + 2)
    out = ROOT / "ubees"
    out.mkdir(exist_ok=True)

    hives = [f"H{i:02d}" for i in range(1, 6)]
    dates = [datetime(2026, 7, 1) + timedelta(days=k) for k in range(0, 20, 2)]

    weight = [
        {
            "hive_id": h,
            "date": d,
            "weight_anomaly_z": round(rng.gauss(0, 1), 3),
            "weight_stddev": round(rng.uniform(0.05, 0.15), 3),
        }
        for h in hives
        for d in dates
    ]
    pd.DataFrame(weight).to_csv(out / "weight_anomaly.csv", index=False)

    acoustic = [
        {
            "hive_id": h,
            "date": d,
            "acoustic_anomaly": round(min(max(rng.gauss(0.3, 0.2), 0), 1), 3),
            "acoustic_stddev": round(rng.uniform(0.05, 0.15), 3),
        }
        for h in hives
        for d in dates
    ]
    pd.DataFrame(acoustic).to_csv(out / "acoustic_anomaly.csv", index=False)

    env = [
        {
            "hive_id": h,
            "date": d,
            "env_prior_score": round(min(max(rng.uniform(0.1, 0.5), 0), 1), 3),
        }
        for h in hives
        for d in dates
    ]
    pd.DataFrame(env).to_csv(out / "env_prior.csv", index=False)


if __name__ == "__main__":
    _ee_samples()
    _kayrros_samples()
    _ubees_samples()
    print("Synthetic samples written under data/samples/{equitable_earth,kayrros,ubees}/")
