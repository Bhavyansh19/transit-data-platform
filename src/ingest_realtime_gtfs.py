"""Fetch, parse, and store BART GTFS-Realtime data."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from google.transit import gtfs_realtime_pb2


TRIP_UPDATES_URL = "https://api.bart.gov/gtfsrt/tripupdate.aspx"
ALERTS_URL = "https://api.bart.gov/gtfsrt/alerts.aspx"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtfs_realtime"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_feed(url):
    """Download one GTFS-Realtime protobuf feed and parse it."""
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
    return feed


def fetch_trip_updates(url=TRIP_UPDATES_URL):
    """Fetch the trip-update feed and return its entities."""
    return fetch_feed(url).entity


def fetch_alerts(url=ALERTS_URL):
    """Fetch the service-alert feed and return its entities."""
    return fetch_feed(url).entity


def parse_trip_update_entity(entity):
    """Convert one protobuf trip update into a simple dictionary."""
    return {
        "entity_id": entity.id,
        "trip_id": entity.trip_update.trip.trip_id,
    }


def parse_trip_updates(entities):
    """Convert all trip-update entities into dictionaries."""
    return [parse_trip_update_entity(entity) for entity in entities]


def parse_alert_entity(entity):
    """Convert one protobuf alert into a simple dictionary."""
    return {"entity_id": entity.id}


def parse_alerts(entities):
    """Convert all alert entities into dictionaries."""
    return [parse_alert_entity(entity) for entity in entities]


def land_raw(records, feed_name, out_dir=RAW_DIR, captured_at=None):
    """Write records to a timestamped JSON file and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)

    if captured_at is None:
        captured_at = datetime.now(timezone.utc)

    timestamp = captured_at.strftime("%Y%m%dT%H%M%SZ")
    output_path = out_dir / f"{feed_name}_{timestamp}.json"
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return output_path


def build_staging_trip_updates(records):
    """Create a clean DataFrame from parsed trip-update records."""
    staging = pd.DataFrame(records, columns=["entity_id", "trip_id"])
    staging = staging.dropna(subset=["entity_id", "trip_id"])
    staging = staging.drop_duplicates(subset=["entity_id"])
    return staging


def process_trip_updates(entities, out_dir=RAW_DIR, captured_at=None):
    """Parse, land, and stage one trip-update feed response."""
    records = parse_trip_updates(entities)
    raw_path = land_raw(
        records,
        feed_name="trip_updates",
        out_dir=out_dir,
        captured_at=captured_at,
    )
    staging = build_staging_trip_updates(records)
    logger.info("Landed %s trip updates to %s", len(records), raw_path)
    logger.info("Built staging table with %s rows", len(staging))
    return staging


if __name__ == "__main__":
    logger.info("Real-time ingestion module is ready.")
    logger.info("Run through tests or call fetch_trip_updates() when the live feed is available.")
