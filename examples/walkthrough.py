"""
End-to-end walkthrough: pick a domain, load its adapter, run the pipeline,
save charts. Run from the repo root with:

    python -m examples.walkthrough --domain equitable_earth
    python -m examples.walkthrough --domain kayrros
    python -m examples.walkthrough --domain ubees

Charts are written to ./out/<domain>/ as SVG (opens in a browser, embeds cleanly
into the per-company README section).
"""
from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path

from src.confidence_pipeline.combine import combine_all
from src.confidence_pipeline.viz import confidence_timeline, disagreement_heatmap


# Per-domain disagreement thresholds. The pipeline is domain-agnostic;
# the domain decides what "too much disagreement" means.
DOMAIN_THRESHOLDS: dict[str, float] = {
    "equitable_earth": 25.0,   # units: (t/ha)^2 on the illustrative biomass scale
    "kayrros": 20.0,            # units: (t/ha)^2 — asset-scale biomass proxy variance
    "ubees": 0.03,              # unitless — variance of intervention-need scores in [0, 1]
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True, choices=list(DOMAIN_THRESHOLDS))
    parser.add_argument("--window", default="1D")
    args = parser.parse_args()

    adapter = import_module(f"adapters.{args.domain}")
    observations = adapter.load_all()
    if not observations:
        raise SystemExit(f"No observations for domain {args.domain} — did you drop CSV samples in data/samples/{args.domain}/ ?")

    # pandas 3.0 offset aliases are lowercase ("1h", "2h", "1d") — normalize so the CLI is forgiving.
    window = args.window.lower()

    estimates = combine_all(
        observations,
        window=window,
        disagreement_threshold=DOMAIN_THRESHOLDS[args.domain],
    )

    out = Path("out") / args.domain
    out.mkdir(parents=True, exist_ok=True)
    confidence_timeline(estimates).save(str(out / "confidence_timeline.svg"))
    disagreement_heatmap(estimates).save(str(out / "disagreement_heatmap.svg"))

    n_flagged = sum(1 for e in estimates if e.flag_review)
    print(
        f"Wrote {len(estimates)} combined estimates ({n_flagged} flagged for review) "
        f"and 2 charts → {out.resolve()}"
    )


if __name__ == "__main__":
    main()
