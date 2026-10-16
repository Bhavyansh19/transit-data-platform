"""Load idempotent GTFS-Realtime snapshots into PostgreSQL."""

import getpass
import json
import logging
import os
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw" / "gtfs_realtime"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def read_trip_update_snapshot(path):
    """Read one landed snapshot and return rows ready for PostgreSQL."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    snapshot_hash = path.stem.removeprefix("trip_updates_")

    return [
        (
            snapshot_hash,
            record["entity_id"],
            record["trip_id"],
            payload["captured_at"],
            path.name,
        )
        for record in payload["records"]
        if record.get("entity_id") and record.get("trip_id")
    ]


def load_trip_update_snapshots(connection, raw_dir=RAW_DIR):
    """Insert landed snapshots without duplicating existing snapshot entities."""
    snapshot_paths = sorted(raw_dir.glob("trip_updates_*.json"))
    rows = [
        row
        for snapshot_path in snapshot_paths
        for row in read_trip_update_snapshot(snapshot_path)
    ]

    if not rows:
        logger.info("No trip-update snapshots found in %s", raw_dir)
        return 0

    with connection.cursor() as cursor:
        execute_values(
            cursor,
            """
            insert into fct_realtime_trip_updates
                (snapshot_hash, entity_id, trip_id, captured_at, source_file)
            values %s
            on conflict (snapshot_hash, entity_id) do nothing
            """,
            rows,
        )

    connection.commit()
    logger.info("Processed %s realtime rows from %s snapshots", len(rows), len(snapshot_paths))
    return len(rows)


def connect_to_postgres():
    """Connect using environment variables with local TransitFlow defaults."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5433"),
        dbname=os.getenv("PGDATABASE", "transitflow"),
        user=os.getenv("PGUSER", getpass.getuser()),
        password=os.getenv("PGPASSWORD", ""),
    )


if __name__ == "__main__":
    with connect_to_postgres() as connection:
        load_trip_update_snapshots(connection)
