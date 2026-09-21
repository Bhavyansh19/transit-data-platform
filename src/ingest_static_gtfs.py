"""Download and load BART's static GTFS schedule data."""

import io
import logging
import zipfile
from pathlib import Path

import pandas as pd
import requests


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


GTFS_URL = "https://www.bart.gov/dev/schedules/google_transit.zip"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs_static"


def download_gtfs(url=GTFS_URL, out_dir=RAW_DIR):
    """Download the GTFS ZIP file and extract it into the raw-data folder."""
    out_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(out_dir)

    return out_dir


def list_entities(gtfs_dir=RAW_DIR):
    """Return the names of all extracted GTFS text files."""
    return sorted(
        path.name
        for path in gtfs_dir.glob("*.txt")
        if path.is_file()
    )
def validate_required_entities(gtfs_dir=RAW_DIR):
    required_entities = {
        "stops.txt",
        "routes.txt",
        "trips.txt",
        "stop_times.txt",
        "calendar.txt",
        "calendar_dates.txt",
    }

    available_entities = set(list_entities(gtfs_dir))
    missing_entities = required_entities - available_entities

    if missing_entities:
        raise FileNotFoundError(
            f"Missing required GTFS files: {sorted(missing_entities)}"
        )

    return True


def validate_required_columns(tables):
    """Check that the core GTFS tables contain the columns we need."""
    required_columns = {
        "stops.txt": {"stop_id", "stop_name", "stop_lat", "stop_lon"},
        "routes.txt": {"route_id", "route_short_name"},
        "trips.txt": {"route_id", "service_id", "trip_id"},
        "stop_times.txt": {
            "trip_id",
            "arrival_time",
            "departure_time",
            "stop_id",
            "stop_sequence",
        },
        "calendar.txt": {"service_id", "monday", "sunday"},
        "calendar_dates.txt": {"service_id", "date", "exception_type"},
    }

    for table_name, expected_columns in required_columns.items():
        actual_columns = set(tables[table_name].columns)
        missing_columns = expected_columns - actual_columns

        if missing_columns:
            raise ValueError(
                f"{table_name} is missing columns: {sorted(missing_columns)}"
            )

    return True


def validate_relationships(tables):
    """Check that foreign-key values exist in their parent GTFS tables."""
    relationships = [
        ("trips.txt", "route_id", "routes.txt", "route_id"),
        ("trips.txt", "service_id", "calendar.txt", "service_id"),
        ("stop_times.txt", "trip_id", "trips.txt", "trip_id"),
        ("stop_times.txt", "stop_id", "stops.txt", "stop_id"),
        ("calendar_dates.txt", "service_id", "calendar.txt", "service_id"),
    ]

    for child_table, child_column, parent_table, parent_column in relationships:
        child_values = set(tables[child_table][child_column].dropna())
        parent_values = set(tables[parent_table][parent_column].dropna())
        missing_values = child_values - parent_values

        if missing_values:
            raise ValueError(
                f"{child_table}.{child_column} contains values missing from "
                f"{parent_table}.{parent_column}: {sorted(missing_values)[:5]}"
            )

    return True


def validate_unique_keys(tables):
    """Check that core GTFS identifiers are unique and not missing."""
    unique_keys = {
        "stops.txt": ["stop_id"],
        "routes.txt": ["route_id"],
        "trips.txt": ["trip_id"],
        "calendar.txt": ["service_id"],
        "stop_times.txt": ["trip_id", "stop_sequence"],
    }

    for table_name, key_columns in unique_keys.items():
        dataframe = tables[table_name]

        if dataframe[key_columns].isna().any().any():
            raise ValueError(
                f"{table_name} has missing values in key columns: {key_columns}"
            )

        duplicate_count = dataframe.duplicated(subset=key_columns).sum()

        if duplicate_count:
            raise ValueError(
                f"{table_name} has {duplicate_count} duplicate key rows for "
                f"{key_columns}"
            )

    return True



def load_entity(entity_name, gtfs_dir=RAW_DIR):
    """Load one GTFS text file into a pandas DataFrame."""
    entity_path = gtfs_dir / entity_name

    if not entity_path.is_file():
        raise FileNotFoundError(f"GTFS file not found: {entity_path}")

    try:
        return pd.read_csv(entity_path)
    except pd.errors.EmptyDataError as error:
        raise ValueError(f"GTFS file is empty: {entity_path}") from error
    except pd.errors.ParserError as error:
        raise ValueError(f"GTFS file has invalid CSV structure: {entity_path}") from error


def load_all_entities(gtfs_dir=RAW_DIR):
    """Load every extracted GTFS text file into a dictionary of DataFrames."""
    tables = {}

    for entity_name in list_entities(gtfs_dir):
        tables[entity_name] = load_entity(entity_name, gtfs_dir)

    return tables


def build_scheduled_stop_events(tables):
    """Build an analytics-ready table of scheduled trip stop events."""
    scheduled_stops = tables["stop_times.txt"].merge(
        tables["stops.txt"][['stop_id', 'stop_name']],
        on="stop_id",
        how="left",
    )
    scheduled_stops = scheduled_stops.merge(
        tables["trips.txt"][['trip_id', 'route_id', 'service_id', 'trip_headsign']],
        on="trip_id",
        how="left",
    )
    scheduled_stops = scheduled_stops.merge(
        tables["routes.txt"][['route_id', 'route_short_name', 'route_long_name']],
        on="route_id",
        how="left",
    )

    return scheduled_stops


if __name__ == "__main__":
    entities = list_entities(RAW_DIR)

    if not entities:
        download_gtfs()
    validate_required_entities(RAW_DIR)
    logger.info("Required GTFS files are present.")

    logger.info("GTFS directory: %s", RAW_DIR)
    logger.info("Entities found: %s", list_entities(RAW_DIR))

    tables = load_all_entities(RAW_DIR)
    validate_required_columns(tables)
    logger.info("Required columns are present.")
    validate_relationships(tables)
    logger.info("GTFS relationships are valid.")
    validate_unique_keys(tables)
    logger.info("GTFS keys are unique and complete.")
    logger.info("Static GTFS ingestion and validation succeeded.")
