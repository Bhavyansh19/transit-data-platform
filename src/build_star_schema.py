"""Build local CSV versions of the TransitFlow star schema."""

import logging
from pathlib import Path

from ingest_static_gtfs import (
    RAW_DIR,
    download_gtfs,
    list_entities,
    load_all_entities,
    validate_relationships,
    validate_required_columns,
    validate_required_entities,
    validate_unique_keys,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent
STAR_SCHEMA_DIR = PROJECT_DIR / "data" / "processed" / "star_schema"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def build_star_schema():
    """Validate static data and write fact/dimension CSV files."""
    if not list_entities(RAW_DIR):
        download_gtfs()

    validate_required_entities(RAW_DIR)
    tables = load_all_entities(RAW_DIR)
    validate_required_columns(tables)
    validate_relationships(tables)
    validate_unique_keys(tables)

    STAR_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

    dimensions = {
        "dim_stops.csv": tables["stops.txt"][[
            "stop_id", "stop_name", "stop_lat", "stop_lon",
            "parent_station", "platform_code",
        ]],
        "dim_routes.csv": tables["routes.txt"][[
            "route_id", "route_short_name", "route_long_name", "route_color",
        ]],
        "dim_trips.csv": tables["trips.txt"][[
            "trip_id", "route_id", "service_id", "trip_headsign", "direction_id",
        ]],
        "dim_service_calendar.csv": tables["calendar.txt"],
    }

    fact = tables["stop_times.txt"][
        [
            "trip_id",
            "stop_sequence",
            "stop_id",
            "arrival_time",
            "departure_time",
        ]
    ].merge(
        tables["trips.txt"][["trip_id", "route_id", "service_id"]],
        on="trip_id",
        how="left",
    )[[
        "trip_id",
        "stop_sequence",
        "stop_id",
        "route_id",
        "service_id",
        "arrival_time",
        "departure_time",
    ]]

    fact.to_csv(STAR_SCHEMA_DIR / "fct_scheduled_stop_events.csv", index=False)

    for filename, dataframe in dimensions.items():
        dataframe.to_csv(STAR_SCHEMA_DIR / filename, index=False)

    logger.info("Wrote star-schema tables to %s", STAR_SCHEMA_DIR)
    return STAR_SCHEMA_DIR


if __name__ == "__main__":
    build_star_schema()
