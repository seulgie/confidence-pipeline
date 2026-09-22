"""
Data contracts for the multi-source confidence pipeline.

Every domain adapter must produce Observations that conform to these schemas.
The pipeline itself never touches domain-specific fields — the adapter's job
is to reduce raw data to a common shape.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Observation(BaseModel):
    """One estimate of the target quantity, from one source, at one location+time.

    The target quantity is domain-defined (biomass, event probability, hive health, ...).
    All that matters for the pipeline is: value, uncertainty, source, when, where.
    """

    unit_id: str = Field(..., description="ID of the operational unit being estimated (parcel, camera-cell, hive)")
    source_id: str = Field(..., description="Which source produced this estimate (e.g., 'sentinel2_ndvi')")
    timestamp: datetime
    value: float = Field(..., description="Point estimate on a comparable scale across sources")
    stddev: float = Field(..., ge=0.0, description="Source-reported or heuristic uncertainty (same units as value)")
    weight_hint: float = Field(
        1.0,
        ge=0.0,
        description="Adapter-supplied prior weight (ground truth > satellite proxy, etc.)",
    )

    @model_validator(mode="after")
    def _check_finite(self):
        if not math.isfinite(self.value):
            raise ValueError("value must be finite")
        if not math.isfinite(self.stddev):
            raise ValueError("stddev must be finite")
        return self


class UnitDefinition(BaseModel):
    """Describes an operational unit — what we're estimating for.

    Kept intentionally minimal. Adapter-specific metadata belongs in `extras`.
    """

    unit_id: str
    unit_kind: Literal["parcel", "camera_cell", "hive"] | str
    extras: dict = Field(default_factory=dict)


class CombinedEstimate(BaseModel):
    """Pipeline output — one confidence-scored estimate per (unit, time-window)."""

    unit_id: str
    window_start: datetime
    window_end: datetime
    n_sources: int
    combined_value: float
    combined_stddev: float
    disagreement: float = Field(..., ge=0.0, description="Weighted variance across per-source point estimates")
    flag_review: bool = Field(..., description="True when disagreement exceeds the domain threshold")
    source_contributions: dict[str, float] = Field(
        default_factory=dict,
        description="source_id → normalized weight share (sums to ~1)",
    )
    source_residuals: dict[str, float] = Field(
        default_factory=dict,
        description="source_id → (source_value − combined_value); where each source disagrees",
    )
