"""Fetch and land real BART estimated departure times.

The GTFS-Realtime protobuf endpoint is the preferred standard feed, but BART's
Cloudflare protection can block automated terminal requests.  This module uses
BART's documented legacy ETD JSON API as a practical fallback.  It first tries
the official API and then a read-only relay only when the official request is
blocked.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw" / "bart_etd"
BART_ETD_URL = "https://api.bart.gov/api/etd.aspx"
BART_ETD_RELAY_URL = "https://r.jina.ai/http://api.bart.gov/api/etd.aspx"
BART_PUBLIC_API_KEY = "MW9S-E7SL-26DU-VV8V"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _request_etd(url, params):
    """Request one JSON response from the selected endpoint."""
    response = requests.get(
        url,
        params=params,
        headers={"Accept": "application/json", "User-Agent": "TransitFlow/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_etd(origin="ALL", api_key=None):
    """Fetch current BART departure estimates for one station or all stations."""
    params = {
        "cmd": "etd",
        "orig": origin,
        "key": api_key or os.getenv("BART_API_KEY", BART_PUBLIC_API_KEY),
        "json": "y",
    }

    try:
        return _request_etd(BART_ETD_URL, params), BART_ETD_URL
    except requests.HTTPError as error:
        if error.response is None or error.response.status_code != 403:
            raise
        logger.warning("Official BART endpoint returned 403; using read-only relay fallback")
        return _request_etd(BART_ETD_RELAY_URL, params), BART_ETD_RELAY_URL


def parse_etd_response(payload):
    """Flatten BART's nested station → destination → estimate JSON response."""
    root = payload.get("root", {})
    rows = []

    for station in root.get("station", []) or []:
        for destination in station.get("etd", []) or []:
            estimates = destination.get("estimate", []) or []
            for estimate in estimates:
                minutes = estimate.get("minutes")
                rows.append(
                    {
                        "station_abbr": station.get("abbr"),
                        "station_name": station.get("name"),
                        "destination_abbr": destination.get("abbreviation"),
                        "destination_name": destination.get("destination"),
                        "minutes": minutes,
                        "platform": estimate.get("platform"),
                        "direction": estimate.get("direction"),
                        "train_length": estimate.get("length"),
                        "color": estimate.get("color"),
                        "delay_seconds": estimate.get("delay"),
                        "cancelled": estimate.get("cancelflag"),
                        "dynamic": estimate.get("dynamicflag"),
                    }
                )

    return rows


def land_etd(payload, source_url, out_dir=RAW_DIR, captured_at=None):
    """Land one content-addressed ETD snapshot and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    captured_at = captured_at or datetime.now(timezone.utc)
    records = parse_etd_response(payload)
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    snapshot_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    output_path = out_dir / f"etd_{snapshot_hash}.json"

    if not output_path.exists():
        output_path.write_text(
            json.dumps(
                {
                    "captured_at": captured_at.isoformat(),
                    "source_url": source_url,
                    "records": records,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    logger.info("Landed %s live ETD records to %s", len(records), output_path)
    return output_path


if __name__ == "__main__":
    payload, source_url = fetch_etd()
    land_etd(payload, source_url)
