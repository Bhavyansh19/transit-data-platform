"""
Week 2 starting point — pull BART's GTFS-Realtime trip updates and alerts.

GTFS-RT feeds are protobuf, not JSON — you'll need the `gtfs-realtime-bindings` package
(`pip install gtfs-realtime-bindings`) to parse them.

Sources:
  Trip updates: http://api.bart.gov/gtfsrt/tripupdate.aspx
  Alerts:       http://api.bart.gov/gtfsrt/alerts.aspx

Known data quality issues to handle here (this is the point of this data source):
  - Some Antioch/Pittsburg Center trip IDs in this feed do NOT match the static schedule's
    trip IDs. Don't assume a naive join between static and real-time data will work.
  - The Oakland Airport Connector does not publish real-time arrival data — handle the
    absence explicitly, don't silently drop or null-fill without noting it.
"""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
import pandas as pd
from google.transit import gtfs_realtime_pb2

TRIP_UPDATES_URL = "https://api.bart.gov/gtfsrt/tripupdate.aspx"
ALERTS_URL = "https://api.bart.gov/gtfsrt/alerts.aspx"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs_realtime"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_trip_updates(url: str = TRIP_UPDATES_URL):
    """Fetch + parse the trip updates protobuf feed. Returns parsed entities."""
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/x-protobuf, application/octet-stream, */*",
        },
        timeout=30,
    )
    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    return feed.entity


def parse_trip_update_entity(entity):
    """Convert one protobuf trip-update entity into a simple dictionary."""
    return {
        "entity_id": entity.id,
        "trip_id": entity.trip_update.trip.trip_id,
    }


def parse_trip_updates(entities):
    """Convert all protobuf trip-update entities into dictionaries."""
    return [parse_trip_update_entity(entity) for entity in entities]


def land_raw(records, feed_name="trip_updates", out_dir=RAW_DIR, captured_at=None):
    """Write parsed real-time records to a timestamped JSON file."""
    out_dir.mkdir(parents=True, exist_ok=True)

    if captured_at is None:
        captured_at = datetime.now(timezone.utc)

    timestamp = captured_at.strftime("%Y%m%dT%H%M%SZ")
    output_path = out_dir / f"{feed_name}_{timestamp}.json"
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    return output_path


def build_staging_trip_updates(records):
    """Convert raw trip-update dictionaries into a clean staging table."""
    staging = pd.DataFrame(records, columns=["entity_id", "trip_id"])
    staging = staging.dropna(subset=["entity_id", "trip_id"])
    staging = staging.drop_duplicates(subset=["entity_id"])

    return staging


def process_trip_updates(entities, out_dir=RAW_DIR, captured_at=None):
    """Run parsing, Bronze landing, and Silver staging for one feed response."""
    records = parse_trip_updates(entities)
    raw_path = land_raw(records, "trip_updates", out_dir, captured_at)
    staging = build_staging_trip_updates(records)

    logger.info("Landed %s raw records to %s", len(records), raw_path)
    logger.info("Built staging table with %s rows", len(staging))

    return staging


def fetch_alerts(url: str = ALERTS_URL):
    """Fetch + parse the service alerts protobuf feed."""
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/x-protobuf, application/octet-stream, */*",
        },
        timeout=30,
    )
    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    return feed.entity


if __name__ == "__main__":
    trip_updates = fetch_trip_updates()
    logger.info("Received %s trip-update entities.", len(trip_updates))

    if trip_updates:
        logger.info("First entity:\n%s", trip_updates[0])
