"""
Kayrros adapter — asset-level forest carbon confidence.

Domain shape:
- unit_id = asset_id (a forest concession / project polygon / MRV parcel)
- target = above-ground biomass proxy at asset scale
- sources:
    1. sentinel2_ndvi   — optical NDVI-derived biomass proxy from Sentinel-2 L2A
                          (aggregated to polygon via zonal statistics)
    2. sentinel1_sar    — SAR C-band VV/VH-derived biomass proxy from Sentinel-1
                          (works through cloud cover — independent signal from optical)
    3. declared_stock   — asset holder's declared baseline; low-weight self-report

Why this shape fits Kayrros's positioning:
    Kayrros markets itself as "source-agnostic" with "data fusion + proprietary
    algorithms." That is the exact operational surface where the disagreement
    between optical (S2) and radar (S1) biomass proxies at asset scale is the
    costliest and most operationally interesting signal — auditors and buyers
    care where the two disagree, not where they average.

Real-data pipeline (planned, not in this stub):
    - STAC discovery: pystac-client against Copernicus / Planetary Computer
    - Raster fetch: stackstac / rioxarray for lazy tile assembly
    - Polygon aggregation: rasterstats or exactextract for zonal statistics
    - S1 preprocessing: gamma nought calibration + speckle filter (RTC preferred)

Expected CSV samples under data/samples/kayrros/ (synthetic while pipeline is stub):
    sentinel2_ndvi.csv   asset_id, date, ndvi_mean, ndvi_stddev
    sentinel1_sar.csv    asset_id, date, sar_biomass, sar_stddev
    declared.csv         asset_id, date, declared_stock
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.confidence_pipeline.schemas import Observation


DATA = Path(__file__).resolve().parent.parent / "data" / "samples" / "kayrros"


def load_ndvi(path: Path | None = None) -> list[Observation]:
    """Sentinel-2 NDVI → biomass proxy at asset scale.

    Illustrative conversion: biomass ≈ 30 × NDVI (t/ha). Real work replaces this
    with a domain-fitted allometric or ML model — but that is scope for after the
    STAC ingest is in place.
    """
    path = path or (DATA / "sentinel2_ndvi.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["asset_id"]),
            source_id="sentinel2_ndvi",
            timestamp=r["date"],
            value=30.0 * float(r["ndvi_mean"]),
            stddev=30.0 * float(r["ndvi_stddev"]),
            weight_hint=1.0,
        )
        for _, r in df.iterrows()
    ]


def load_sar(path: Path | None = None) -> list[Observation]:
    """Sentinel-1 SAR VV/VH → biomass proxy at asset scale.

    Cloud-independent alternative source. Illustrative sample values are in the
    same biomass units as the NDVI proxy so the pipeline can combine them directly.
    """
    path = path or (DATA / "sentinel1_sar.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["asset_id"]),
            source_id="sentinel1_sar",
            timestamp=r["date"],
            value=float(r["sar_biomass"]),
            stddev=float(r["sar_stddev"]),
            weight_hint=1.0,
        )
        for _, r in df.iterrows()
    ]


def load_declared(path: Path | None = None) -> list[Observation]:
    """Asset holder's declared baseline — low weight, elevated stddev."""
    path = path or (DATA / "declared.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["asset_id"]),
            source_id="declared_stock",
            timestamp=r["date"],
            value=float(r["declared_stock"]),
            stddev=float(r["declared_stock"]) * 0.3,
            weight_hint=0.3,
        )
        for _, r in df.iterrows()
    ]


def load_all() -> list[Observation]:
    return load_ndvi() + load_sar() + load_declared()
