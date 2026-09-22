"""
Weighted evidence combination + disagreement metric.

Design choices (documented here on purpose — this is the file a CTO reads first):

1. Combination = inverse-variance weighted mean, tempered by the adapter's weight_hint.
   Sources with lower stddev pull the estimate more; ground truth wins by default.

2. Disagreement = weighted variance of the *point estimates* (not their uncertainties).
   This is the signal that says "the sources are telling different stories" — the exact
   thing an operator wants surfaced before trusting the combined number.

3. flag_review = disagreement above a per-domain threshold (config, not code).
   The pipeline doesn't decide what "too much disagreement" means — the domain does.

Explicitly NOT Bayesian model averaging, NOT Shapley attribution, NOT a fancy ensemble.
Those add complexity that a 4-hour MVP can't defend, and they hide the disagreement
signal that is the whole point of this pipeline.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import datetime

from .schemas import CombinedEstimate, Observation


def _weight(obs: Observation) -> float:
    """Inverse-variance weight, softened by an adapter-provided hint."""
    variance = obs.stddev ** 2 + 1e-9
    return obs.weight_hint / variance


def combine_window(
    observations: list[Observation],
    unit_id: str,
    window_start: datetime,
    window_end: datetime,
    disagreement_threshold: float,
) -> CombinedEstimate:
    """Combine one time-window's observations for one unit."""
    if not observations:
        raise ValueError("combine_window: no observations")

    weights = [_weight(o) for o in observations]
    total_w = sum(weights)
    if total_w == 0:
        raise ValueError("combine_window: zero total weight")

    normalized = [w / total_w for w in weights]
    combined_value = sum(w * o.value for w, o in zip(normalized, observations))

    # Weighted variance of point estimates — the disagreement signal.
    disagreement = sum(
        w * (o.value - combined_value) ** 2 for w, o in zip(normalized, observations)
    )

    # Combined uncertainty = inverse of total precision.
    combined_stddev = math.sqrt(1.0 / total_w)

    # Per-source bookkeeping for attribution.
    contributions = {o.source_id: w for o, w in zip(observations, normalized)}
    residuals = {o.source_id: o.value - combined_value for o in observations}

    return CombinedEstimate(
        unit_id=unit_id,
        window_start=window_start,
        window_end=window_end,
        n_sources=len(observations),
        combined_value=combined_value,
        combined_stddev=combined_stddev,
        disagreement=disagreement,
        flag_review=disagreement > disagreement_threshold,
        source_contributions=contributions,
        source_residuals=residuals,
    )


def combine_all(
    observations: Iterable[Observation],
    window: str = "1D",
    disagreement_threshold: float = 1.0,
) -> list[CombinedEstimate]:
    """Group observations by (unit_id, time-window) and combine each group.

    `window` is a pandas offset alias — "1D", "1H", "15min", etc. Keeps the API narrow.
    """
    import pandas as pd

    rows = [o.model_dump() for o in observations]
    if not rows:
        return []
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["window_start"] = df["timestamp"].dt.floor(window)

    out: list[CombinedEstimate] = []
    for (unit_id, ws), grp in df.groupby(["unit_id", "window_start"]):
        obs = [Observation(**r) for r in grp.drop(columns=["window_start"]).to_dict(orient="records")]
        we = ws + pd.Timedelta(window)
        out.append(
            combine_window(
                observations=obs,
                unit_id=str(unit_id),
                window_start=ws.to_pydatetime(),
                window_end=we.to_pydatetime(),
                disagreement_threshold=disagreement_threshold,
            )
        )
    return out
