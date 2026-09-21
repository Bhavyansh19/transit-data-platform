"""Run the local TransitFlow MVP pipeline."""

import logging
from pathlib import Path

from ingest_static_gtfs import (
    RAW_DIR,
    build_scheduled_stop_events,
    download_gtfs,
    list_entities,
    load_all_entities,
    validate_relationships,
    validate_required_columns,
    validate_required_entities,
    validate_unique_keys,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def run_static_pipeline():
    """Download if needed, validate, transform, and write the static output."""
    if not list_entities(RAW_DIR):
        download_gtfs()

    validate_required_entities(RAW_DIR)
    tables = load_all_entities(RAW_DIR)
    validate_required_columns(tables)
    validate_relationships(tables)
    validate_unique_keys(tables)

    scheduled_stop_events = build_scheduled_stop_events(tables)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    staging_path = PROCESSED_DIR / "scheduled_stop_events.csv"
    scheduled_stop_events.to_csv(staging_path, index=False)

    route_summary = (
        scheduled_stop_events.groupby(
            ["route_id", "route_short_name", "route_long_name"],
            dropna=False,
        )
        .agg(
            scheduled_stop_events=("stop_id", "size"),
            scheduled_trips=("trip_id", "nunique"),
            scheduled_stops=("stop_id", "nunique"),
        )
        .reset_index()
        .sort_values("scheduled_stop_events", ascending=False)
    )
    mart_path = PROCESSED_DIR / "route_schedule_summary.csv"
    route_summary.to_csv(mart_path, index=False)

    logger.info("Wrote %s rows to %s", len(scheduled_stop_events), staging_path)
    logger.info("Wrote %s route summaries to %s", len(route_summary), mart_path)
    return staging_path, mart_path


if __name__ == "__main__":
    run_static_pipeline()