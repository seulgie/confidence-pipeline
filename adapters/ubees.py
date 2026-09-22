"""
Ubees adapter — hive intervention-need confidence.

Domain shape:
- unit_id = hive_id
- target = "intervention need" score in [0, 1] (higher = more likely something is wrong)
- sources:
    1. weight_anomaly    — deviation of hive weight from expected seasonal profile
    2. acoustic_anomaly  — deviation of hive sound spectrum from baseline
    3. env_prior         — weather + surrounding land use contribution to a prior anomaly rate

Expected CSV samples under data/samples/ubees/:
    weight_anomaly.csv    hive_id, date, weight_anomaly_z, weight_stddev
    acoustic_anomaly.csv  hive_id, date, acoustic_anomaly, acoustic_stddev
    env_prior.csv         hive_id, date, env_prior_score
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from src.confidence_pipeline.schemas import Observation


DATA = Path(__file__).resolve().parent.parent / "data" / "samples" / "ubees"


def _squash(z: float) -> float:
    """|z| → (0, 1) via a symmetric sigmoid. Illustrative, replace with a domain model."""
    return 1.0 / (1.0 + math.exp(-abs(z)))


def load_weight(path: Path | None = None) -> list[Observation]:
    path = path or (DATA / "weight_anomaly.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["hive_id"]),
            source_id="weight_anomaly",
            timestamp=r["date"],
            value=_squash(float(r["weight_anomaly_z"])),
            stddev=float(r["weight_stddev"]),
            weight_hint=1.0,
        )
        for _, r in df.iterrows()
    ]


def load_acoustic(path: Path | None = None) -> list[Observation]:
    path = path or (DATA / "acoustic_anomaly.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["hive_id"]),
            source_id="acoustic_anomaly",
            timestamp=r["date"],
            value=float(r["acoustic_anomaly"]),
            stddev=float(r["acoustic_stddev"]),
            weight_hint=1.0,
        )
        for _, r in df.iterrows()
    ]


def load_context(path: Path | None = None) -> list[Observation]:
    path = path or (DATA / "env_prior.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return [
        Observation(
            unit_id=str(r["hive_id"]),
            source_id="env_prior",
            timestamp=r["date"],
            value=float(r["env_prior_score"]),
            stddev=0.2,
            weight_hint=0.5,
        )
        for _, r in df.iterrows()
    ]


def load_all() -> list[Observation]:
    return load_weight() + load_acoustic() + load_context()
