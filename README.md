# TransitFlow Data Platform

A batch + real-time data pipeline built on BART's public GTFS and GTFS-Realtime feeds —
built as a learning project to go from fresher to job-ready as a Data Engineer.

Status: 🚧 in progress — see `docs/project-plan.md` for the week-by-week build log.

---

## Architecture

```text
BART GTFS (static schedule, .zip)      BART GTFS-Realtime (trip updates, alerts)
            │                                       │
            ▼                                       ▼
      Python ingestion  ─────────────────────  Python ingestion
            │                                       │
            └───────────────► data/raw/ ◄───────────┘
                                   │
                                   ▼
                         Staging (cleaned, typed,
                          deduplicated, validated)
                                   │
                                   ▼
                        Data Warehouse (raw → staging → marts)
                                   │
                                   ▼
                          dbt models + tests
                                   │
                                   ▼
                      Airflow DAG (orchestration,
                       retries, scheduling, logs)
                                   │
                                   ▼
                        Marts (fact/dim tables,
                         ready for querying)
```

(Diagram will be swapped for a real one once the pipeline is running end-to-end — update this
when the Airflow DAG is live.)

## Tech stack

| Layer | Tool | Notes |
|---|---|---|
| Ingestion | Python (`requests`, `pandas`) | Pulls static GTFS zip + GTFS-RT protobuf feeds |
| Storage (raw) | Local / S3 | Starts local, moves to S3 in Week 5 |
| Warehouse | Snowflake (or Postgres locally first) | raw → staging → marts |
| Transformation | dbt | Models, tests, documentation |
| Orchestration | Airflow | DAGs, retries, scheduling |
| Modeling | Star schema | Fact: trip updates. Dimensions: stations, routes, calendar |
| Version control | Git / GitHub | This repo |

## What this pipeline does

Ingests BART's static GTFS schedule (routes, stops, trips, calendar) alongside the
GTFS-Realtime feeds (trip updates, service alerts), reconciles the two against each other,
handles the feed's known real-world inconsistencies (see **Data quality** below), and lands
clean, queryable fact/dimension tables in a warehouse — orchestrated end-to-end by Airflow and
transformed with dbt.

## Data source

- **Static schedule (GTFS):** `https://www.bart.gov/dev/schedules/google_transit.zip`
- **Real-time trip updates (GTFS-RT):** `http://api.bart.gov/gtfsrt/tripupdate.aspx`
- **Real-time alerts (GTFS-RT):** `http://api.bart.gov/gtfsrt/alerts.aspx`
- No registration required; usage subject to BART's developer license agreement.
- **Known real-world data issues to handle** (this is the point of picking a messy source):
  - Some Antioch/Pittsburg Center GTFS-RT trip IDs do not match the static schedule's trip IDs
    — needs reconciliation logic, not a naive join.
  - The Oakland Airport Connector does not publish real-time arrival data — needs explicit
    handling (null-safe joins, documented gap) rather than silently dropping those rows.

## Data model

- **Fact table:** `fct_trip_updates` — one row per real-time trip update event
- **Dimension tables:** `dim_stations`, `dim_routes`, `dim_calendar`
- SCD strategy: Type 2 on `dim_routes` / `dim_stations` if schedule changes are observed during
  the project — documented here once implemented, not assumed up front.

## Pipeline design

- **Ingestion:** Python script(s) in `src/` pull the static GTFS zip and the GTFS-RT feeds on a
  schedule, landing raw files in `data/raw/`.
- **Batch vs. incremental:** static schedule is a full reload (it changes rarely); GTFS-RT is
  ingested incrementally on a short interval.
- **Transformation:** dbt models in `dbt/models/staging` and `dbt/models/marts`.
- **Orchestration:** Airflow DAG in `dags/` — ingestion → staging → marts, with retries and
  failure alerts.

## Data quality

- Tests defined in `dbt/` (not-null, unique, relationships, accepted values).
- Explicit handling for the two known BART feed inconsistencies listed above under **Data
  source** — this is the main "real-world mess" this project demonstrates.
- Row counts and null-rate checks logged per run (numbers land in **Numbers** below once
  measured).

## Failure handling

- Airflow retries with backoff on task failure.
- Idempotent ingestion — re-running a task for the same time window does not duplicate data.
- Documented here as it's actually implemented, not speculated in advance.

## Numbers

_TBD — filled in with real, measured values once the pipeline has actual runs. Do not
pre-fill this with invented numbers._

| Metric | Value |
|---|---|
| Rows ingested / day | TBD |
| Pipeline latency (ingest → queryable) | TBD |
| dbt test pass rate | TBD |
| DAG success rate (last 30 runs) | TBD |

## Milestones

- [ ] Week 1 — repo, Git, first Python ingestion script (raw landing)
- [ ] Week 2 — DE fundamentals applied: incremental ingestion, idempotency
- [ ] Week 3 — data model designed (star schema, fact/dim)
- [ ] Week 4 — warehouse loaded, dbt models + tests live
- [ ] Week 5 — pipeline moved onto AWS (S3, Glue, Redshift/Athena)
- [ ] Week 6 — Airflow DAG orchestrating the full pipeline end-to-end
- [ ] Post-week-6 — PySpark/Databricks or Kafka additions, only if a target JD calls for it

## Interview talking points

_Fill this in as the project develops — this is what you'll actually say in interviews._

- Why GTFS + GTFS-RT as a source (real inconsistencies, not a clean CSV)
- How the two known BART feed issues were handled and why
- Why star schema over snowflake for this data
- Why ELT here / where ETL made more sense instead
- One thing that broke in the pipeline and how it was diagnosed and fixed

---

## Setup

```bash
git clone <this-repo>
cd transit-data-platform
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # add as dependencies accumulate
```

## Repo structure

```text
transit-data-platform/
├── README.md
├── docs/
│   └── project-plan.md      # week-by-week build log, source of truth for status
├── src/                      # ingestion scripts
├── dags/                     # Airflow DAGs
├── dbt/                      # dbt project (models/staging, models/marts)
├── tests/                    # unit tests for ingestion/transformation code
├── infra/                    # IaC / AWS setup notes, once Week 5 starts
├── data/
│   ├── raw/                  # gitignored — raw landed files
│   └── processed/            # gitignored — processed/local output
└── .gitignore
```
