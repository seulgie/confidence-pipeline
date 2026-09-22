"""
Two canonical visualizations. Everything else is noise.

1. Confidence timeline — one line per unit, band = ±combined_stddev,
   flagged windows marked. Answers: "when should I trust the number?"

2. Disagreement heatmap — units on Y, sources on X, cell = residual (diverging).
   Answers: "when I don't trust the number, which source is the outlier?"

Both are Altair, both SVG-friendly, both readable in a repo preview.

Palette note: sticks with Altair defaults for the categorical axis, uses a diverging
red-blue scale centred at 0 for the residual heatmap (semantic: negative = source
pulls down, positive = source pulls up). Refine per company if needed.
"""
from __future__ import annotations

from .attribute import dissect_many
from .schemas import CombinedEstimate


def confidence_timeline(estimates: list[CombinedEstimate]):
    import altair as alt
    import pandas as pd

    if not estimates:
        raise ValueError("confidence_timeline: no estimates to plot")

    df = pd.DataFrame([e.model_dump() for e in estimates])
    df["timestamp"] = pd.to_datetime(df["window_start"])
    df["lower"] = df["combined_value"] - df["combined_stddev"]
    df["upper"] = df["combined_value"] + df["combined_stddev"]

    base = alt.Chart(df).encode(
        x=alt.X("timestamp:T", title="Time"),
        color=alt.Color("unit_id:N", title="Unit"),
    )

    band = base.mark_area(opacity=0.2).encode(
        y=alt.Y("lower:Q", title="Combined estimate"),
        y2="upper:Q",
    )
    line = base.mark_line().encode(y="combined_value:Q")
    flags = (
        base.transform_filter("datum.flag_review")
        .mark_point(size=90, filled=True, shape="triangle-up")
        .encode(y="combined_value:Q")
    )
    return (band + line + flags).properties(
        width=640,
        height=280,
        title="Confidence timeline (bands = ±σ, ▲ = flagged for review)",
    )


def disagreement_heatmap(estimates: list[CombinedEstimate]):
    import altair as alt

    df = dissect_many(estimates)
    if df.empty:
        raise ValueError("disagreement_heatmap: no rows to plot")

    return (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X("source_id:N", title="Source"),
            y=alt.Y("unit_id:N", title="Unit"),
            color=alt.Color(
                "residual:Q",
                scale=alt.Scale(scheme="redblue", domainMid=0),
                title="Residual (source − combined)",
            ),
            tooltip=["unit_id", "source_id", "contribution", "residual", "flag_review"],
        )
        .properties(
            width=420,
            height=280,
            title="Where sources disagree (positive = source pulls up)",
        )
    )
