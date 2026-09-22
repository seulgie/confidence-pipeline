# Multi-source Confidence & Attribution Pipeline

> A small data engineering pipeline that takes heterogeneous, noisy estimates of the
> same operational quantity and produces a confidence-scored decision — with the
> disagreement across sources kept as a first-class pipeline output, not absorbed
> into a downstream model.

## Positioning

This is a **data engineering** artifact, not a modeling one. The opinionated move —
keep disagreement observable at the pipeline layer rather than resolving it inside
a fusion model — is a **data contract decision**. Any modeling that consumes the
outputs of this pipeline gets a richer, more auditable input than a single fused
number would provide.

## Why this shape

Operational teams (carbon verifiers, city surveillance operators, farm/beekeeping ops)
share one problem: **the answer they act on comes from multiple sources that don't
agree, and the cost of a wrong answer is real (fraud, false alarm, spoilt hive).**

Most pipelines resolve the disagreement inside the model and hand out a single number.
This one keeps the disagreement first-class — it surfaces where sources conflict, how
much each source paid for the final value, and flags the units where operators should
step in before trusting the number.

## What it does

1. Each domain adapter reduces raw data (satellite / sensors / documents / video events)
   to a stream of **Observations** — a common schema:
   `(unit_id, source_id, timestamp, value, stddev, weight_hint)`.
2. The pipeline groups observations by `(unit_id, time-window)` and produces a
   **CombinedEstimate** — inverse-variance weighted mean tempered by adapter weights,
   plus a disagreement metric (weighted variance of the point estimates).
3. Each combined estimate carries per-source **contributions** (weight share) and
   **residuals** (how far each source is from the consensus) — the attribution layer.
4. Two visualizations render the outputs:
   - **Confidence timeline** — band = ±σ, ▲ = flagged for review
   - **Disagreement heatmap** — units × sources, cell = residual

## What it deliberately is NOT

- Not Bayesian model averaging (opacity buys nothing here).
- Not Shapley attribution (weighted contribution is already legible; Shapley is a
  research move, not a 4-hour MVP move).
- Not a deployed dashboard (repo + notebook = the deliverable).
- Not a live satellite ingest (pre-computed CSVs — rabbit hole guard).

## Repo layout

```
src/confidence_pipeline/     ← the reusable shell (does not know about any domain)
  schemas.py                   Pydantic data contracts
  combine.py                   weighted combine + disagreement metric
  attribute.py                 per-source contribution + residual bookkeeping
  viz.py                       the two charts
adapters/                    ← per-domain data loaders (this is what changes per company)
  equitable_earth.py           carbon claim confidence: S2 NDVI + ground plot + declared
  kayrros.py                   asset forest carbon: S2 NDVI + S1 SAR + declared
  ubees.py                     hive intervention need: sensors + environmental prior
examples/walkthrough.py      ← run one domain end-to-end, write charts to out/<domain>/
data/samples/<domain>/       ← synthetic CSV samples per domain (regenerable)
```

The EE and Kayrros adapters share the same raster→polygon zonal-stats backbone;
they differ only in which sources they combine (NDVI + ground truth + declared
vs NDVI + SAR + declared). Ubees uses the same combine/attribute shell with
a different source stack (sensor + weather + land use).

## Setup (Windows / miniconda / PowerShell)

```powershell
conda env create -f environment.yml
conda activate confidence-pipeline
python data/samples/generate_synthetic.py            # first-run only: seeds tiny CSVs so the walkthrough has data
python -m examples.walkthrough --domain equitable_earth
python -m examples.walkthrough --domain kayrros
python -m examples.walkthrough --domain ubees
```

Charts land in `out/<domain>/`. Note that pandas 3.0's offset aliases are lowercase (`1h`, `2h`, `1d`); the walkthrough normalizes for you, but SQL/dbt code you write yourself should use the same convention.

---

## Per-company write-up

*(This section is what the CTO reads. Swap it per branch — the shell above stays.)*

### Problem I saw
<!-- 1 paragraph — the specific operational problem THIS company faces, in their language as much as possible. -->

TODO

### Architectural choice + why
<!-- 1 paragraph — why this pipeline shape fits their problem. What would break if you resolved disagreement inside the model. -->

TODO

### What I built + tradeoffs
<!-- 1 paragraph — what this MVP actually is (short), what you deliberately left out, and what that costs. -->

TODO

### What I'd build next if we talk
<!-- 1 sentence — the natural extension you're curious about. This is the hook. -->

TODO
