"""
Attribution layer: given a combined estimate, expose which sources drove it
and where they disagreed.

This is not Shapley. It is transparent weighted-contribution bookkeeping,
kept simple on purpose:

- Contribution = normalized weight of the source in the inverse-variance mean.
  (How much of the combined value did this source pay for?)
- Residual = source_value − combined_value.
  (How much does this source disagree with the consensus?)

A CTO reading the pipeline should be able to point at any flagged unit and say
"this satellite reading pulled the estimate up, and this ground plot residual is
why we flagged it" — without needing a model card.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .schemas import CombinedEstimate

if TYPE_CHECKING:
    import pandas as pd


def dissect(estimate: CombinedEstimate) -> list[dict]:
    """Return per-source rows describing contribution and residual.

    Downstream: this feeds a table + a heatmap over units × sources.
    """
    rows = []
    for source_id, contribution in estimate.source_contributions.items():
        rows.append(
            {
                "unit_id": estimate.unit_id,
                "window_start": estimate.window_start,
                "source_id": source_id,
                "contribution": contribution,
                "residual": estimate.source_residuals.get(source_id, 0.0),
                "flag_review": estimate.flag_review,
            }
        )
    return rows


def dissect_many(estimates: list[CombinedEstimate]) -> "pd.DataFrame":
    """Flatten a batch of combined estimates into a source-level long dataframe."""
    import pandas as pd

    rows: list[dict] = []
    for e in estimates:
        rows.extend(dissect(e))
    return pd.DataFrame(rows)
