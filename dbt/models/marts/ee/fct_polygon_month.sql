{{ config(materialized='table') }}

-- Fact table: monthly biomass proxy + DQ per parcel.
-- One row per (parcel_id, month).
--
-- Design decision to record in the README:
--   Where does the DQ (combined + disagreement + flag_review) computation live?
--   Option A — inside dbt via a Python model (single graph, fiddly)
--   Option B — inside Airflow, upstream of dbt (recommended — DQ math stays in
--              Python, Airflow orchestrates, dbt stays pure SQL)
--
-- TODO once Option B chosen:
--   join stg_s2_ndvi, stg_ground_plots, stg_declared, stg_ee_dq

select
    parcel_id,
    date_trunc('month', observation_date) as month,
    avg(ndvi_mean)         as ndvi_month_mean,
    stddev_samp(ndvi_mean) as ndvi_month_stddev,
    count(*)               as n_obs
    -- TODO: combined_biomass, disagreement, flag_review
from
    {{ ref('stg_s2_ndvi') }}
group by 1, 2