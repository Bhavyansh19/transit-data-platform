"""Load landed BART ETD snapshots into PostgreSQL."""

import getpass
import json
import logging
import os
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw" / "bart_etd"
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def read_etd_snapshot(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    snapshot_hash = path.stem.removeprefix("etd_")
    rows = []

    for record_number, record in enumerate(payload["records"]):
        rows.append(
            (
                snapshot_hash,
                record_number,
                record.get("station_abbr"),
                record.get("station_name"),
                record.get("destination_abbr"),
                record.get("destination_name"),
                record.get("minutes"),
                record.get("platform"),
                record.get("direction"),
                record.get("train_length"),
                record.get("color"),
                record.get("delay_seconds"),
                record.get("cancelled"),
                record.get("dynamic"),
                payload["captured_at"],
                path.name,
            )
        )
    return rows


def load_etd_snapshots(connection, raw_dir=RAW_DIR):
    rows = [
        row
        for path in sorted(raw_dir.glob("etd_*.json"))
        for row in read_etd_snapshot(path)
    ]
    if not rows:
        logger.info("No ETD snapshots found in %s", raw_dir)
        return 0

    with connection.cursor() as cursor:
        execute_values(
            cursor,
            """
            insert into fct_realtime_etd
                (snapshot_hash, record_number, station_abbr, station_name,
                 destination_abbr, destination_name, minutes, platform,
                 direction, train_length, color, delay_seconds, cancelled,
                 dynamic, captured_at, source_file)
            values %s
            on conflict (snapshot_hash, record_number) do nothing
            """,
            rows,
        )
    connection.commit()
    logger.info("Loaded %s ETD rows from %s snapshots", len(rows), len(list(raw_dir.glob("etd_*.json"))))
    return len(rows)


def connect_to_postgres():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5433"),
        dbname=os.getenv("PGDATABASE", "transitflow"),
        user=os.getenv("PGUSER", getpass.getuser()),
        password=os.getenv("PGPASSWORD", ""),
    )


if __name__ == "__main__":
    with connect_to_postgres() as connection:
        load_etd_snapshots(connection)
