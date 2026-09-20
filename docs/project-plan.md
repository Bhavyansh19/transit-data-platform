# Project plan / build log

Source of truth for what's actually been done — update this as you go, don't let it drift from
the code. Each entry should be short: what shipped, what broke, what's next.

## Week 1 — SQL + Python foundations, Git, project skeleton
- [ ] Repo created, pushed to GitHub
- [x] Static GTFS snapshot downloaded and inspected
- [x] Entities/tables in the GTFS zip identified (routes, stops, trips, stop_times, calendar)
- [x] Python ingestion v0 — download + unzip + load into pandas
- [ ] First commit made

**Notes:**

- Downloaded the BART static GTFS snapshot into `data/raw/gtfs_static/`.
- Verified the six core tables and their key relationships.
- Added pandas loading for all extracted GTFS entities, validation, logging, and automated tests.

## Week 2 — DE fundamentals, ingestion hardening
- [ ] GTFS-RT trip updates pulled (protobuf → parsed)
- [ ] Raw landing for both static + real-time feeds
- [ ] Idempotency: re-running ingestion doesn't duplicate rows
- [ ] Documented the two known BART feed inconsistencies and how they show up in the raw data

**Notes:**

## Week 3 — Data modeling
- [ ] Star schema designed: fact_trip_updates + dim_stations, dim_routes, dim_calendar
- [ ] Schema documented in README

**Notes:**

## Week 4 — Warehouse + dbt
- [ ] Warehouse chosen and set up (Snowflake trial or local Postgres)
- [ ] Raw → staging → marts dbt models built
- [ ] dbt tests added (not-null, unique, relationships)

**Notes:**

## Week 5 — AWS
- [ ] Raw files landing in S3
- [ ] Glue crawler/catalog set up
- [ ] Querying via Redshift or Athena

**Notes:**

## Week 6 — Airflow
- [ ] DAG built: ingest → staging → marts
- [ ] Retries + failure handling configured
- [ ] End-to-end run succeeded at least once
- [ ] README "Numbers" section filled with real measured values
- [ ] Started applying

**Notes:**

## Post-week-6
- [ ] PySpark / Databricks added — only if a target JD asked for it
- [ ] Kafka added — only if a target JD asked for it
