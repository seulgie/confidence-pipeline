{{ config(materialized='view') }}

-- Staging: per-polygon-per-date NDVI observations from the EE Airflow ingest.
-- TODO (in order):
-- 1. dbt run --select stg_s2_ndvi (should just work on the mock CSV)
-- 2. Add schema.yml with source freshness test
-- 3. Swap read_csv_auto → read_parquet('s3://staged/ee/observations/*.parquet')
--    once the DAG has produced a real slice
-- 4. Add pixel_count and cloud_frac columns

select
    parcel_id,
    date::date              as observation_date,
    ndvi_mean,
    ndvi_stddev,
    'sentinel2_ndvi'        as source_id
from
    read_csv_auto('../data/samples/equitable_earth/sentinel2_ndvi.csv')