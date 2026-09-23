# dbt model scaffolding

The `ee/` folders under `staging/` and `marts/` hold the example.
Duplicate that pattern for the other two domains as you build them:

models/
├── staging/
│   ├── ee/{stg_s2_ndvi.sql ✓, stg_ground_plots.sql TODO, stg_declared.sql TODO}
│   ├── kayrros/{stg_s2_ndvi.sql TODO, stg_s1_sar.sql TODO, stg_declared.sql TODO}
│   └── ubees/{stg_weight.sql TODO, stg_acoustic.sql TODO, stg_env.sql TODO}
├── marts/
│   ├── ee/fct_polygon_month.sql ✓
│   ├── kayrros/fct_asset_month.sql TODO
│   └── ubees/fct_hive_daily.sql TODO

Each staging model = one parquet source, one view. Keep boring.
Each mart = one grain (parcel-month, asset-month, hive-day).
Add schema.yml files (not_null, unique, accepted_values) once models compile.