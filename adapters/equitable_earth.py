"""
Equitable Earth adapter — carbon claim confidence for nature-based projects.

Domain shape:
- unit_id = project polygon (or sub-parcel)
- target = biomass proxy (t/ha) or an NDVI-derived carbon-density signal
- sources:
    1. sentinel2_ndvi   — pre-computed NDVI aggregated to polygon, loaded from CSV.
                          (Do NOT go live to STAC in the MVP — rabbit hole.)
    2. ground_plot      — mock plot measurements; adapter treats as high-weight ground truth.
    3. project_declared — project's self-reported baseline; low-weight self-report.

Expected CSV samples under data/samples/equitable_earth/:
    sentinel2_ndvi.csv   parcel_id, date, ndvi_mean, ndvi_stddev
    ground_plots.csv     parcel_id, date, plot_biomass, plot_stddev
    declared.csv         parcel_id, date, declared_biomass
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.confidence_pipeline.schemas import Observation


DATA = Path(__file__).resolve().parent.parent / "data" / "samples" / "equitable_earth"


def load_ndvi(path: Path | None = None) -> list[Observation]:
    path = path or (DATA / "sentinel2_ndvi.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    # Illustrative biomass proxy: biomass ≈ 30 × NDVI.
    # The write-up must state this is a proxy, not a claim.
    return [
        Observation(
            unit_id=str(r["parcel_id"]),
            source_id="sentinel2_ndvi",
            timestamp=r["date"],
            value=30.0 * r["ndvi_mean"],
            stddev=30.0 * r["ndvi_stddev"],
            weight_hint=1.0,
        )
        for _, r in df.iterrows()
    ]


def load_ground_plots(path: Path | None = None) -> list[Observation]:
    path = path or (DATA / "ground_plots.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["parcel_id"]),
            source_id="ground_plot",
            timestamp=r["date"],
            value=float(r["plot_biomass"]),
            stddev=float(r["plot_stddev"]),
            weight_hint=3.0,  # ground truth prior
        )
        for _, r in df.iterrows()
    ]


def load_declared(path: Path | None = None) -> list[Observation]:
    path = path or (DATA / "declared.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["parcel_id"]),
            source_id="project_declared",
            timestamp=r["date"],
            value=float(r["declared_biomass"]),
            stddev=float(r["declared_biomass"]) * 0.3,  # discount for self-report noise
            weight_hint=0.3,
        )
        for _, r in df.iterrows()
    ]


def load_all() -> list[Observation]:
    return load_ndvi() + load_ground_plots() + load_declared()
