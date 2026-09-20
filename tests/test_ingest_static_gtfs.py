"""Week 1-2: basic tests for the static ingestion script."""

from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest

from src.ingest_static_gtfs import (
    download_gtfs,
    list_entities,
    load_entity,
    validate_required_columns,
    validate_relationships,
    validate_unique_keys,
)


class FakeResponse:
    content = None

    def raise_for_status(self):
        return None


def test_download_gtfs_extracts_archive(monkeypatch, tmp_path: Path):
    archive_path = tmp_path / "bart.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("stops.txt", "stop_id,stop_name\n1,12th St\n")
        archive.writestr("routes.txt", "route_id,route_short_name\n1,Red\n")

    response = FakeResponse()
    response.content = archive_path.read_bytes()
    monkeypatch.setattr("src.ingest_static_gtfs.requests.get", lambda *args, **kwargs: response)

    output_dir = download_gtfs("https://example.test/bart.zip", tmp_path / "gtfs_static")

    assert output_dir == tmp_path / "gtfs_static"
    assert list_entities(output_dir) == ["routes.txt", "stops.txt"]


def test_load_entity_reads_csv(tmp_path: Path):
    stops_path = tmp_path / "stops.txt"
    stops_path.write_text("stop_id,stop_name\n1,12th St\n")

    stops = load_entity("stops.txt", tmp_path)

    assert list(stops.columns) == ["stop_id", "stop_name"]
    assert len(stops) == 1


def test_validation_functions_accept_valid_tables():
    tables = {
        "stops.txt": pd.DataFrame(
            {"stop_id": ["S1"], "stop_name": ["Station"], "stop_lat": [1.0], "stop_lon": [2.0]}
        ),
        "routes.txt": pd.DataFrame(
            {"route_id": ["R1"], "route_short_name": ["Red"]}
        ),
        "trips.txt": pd.DataFrame(
            {"route_id": ["R1"], "service_id": ["W1"], "trip_id": ["T1"]}
        ),
        "stop_times.txt": pd.DataFrame(
            {
                "trip_id": ["T1"],
                "arrival_time": ["08:00:00"],
                "departure_time": ["08:01:00"],
                "stop_id": ["S1"],
                "stop_sequence": [1],
            }
        ),
        "calendar.txt": pd.DataFrame(
            {"service_id": ["W1"], "monday": [1], "sunday": [0]}
        ),
        "calendar_dates.txt": pd.DataFrame(
            {"service_id": ["W1"], "date": [20260920], "exception_type": [2]}
        ),
    }

    assert validate_required_columns(tables) is True
    assert validate_relationships(tables) is True
    assert validate_unique_keys(tables) is True


def test_required_columns_reject_missing_column():
    tables = {
        "stops.txt": pd.DataFrame(
            {"stop_id": ["S1"], "stop_name": ["Station"], "stop_lat": [1.0]}
        )
    }

    with pytest.raises(ValueError, match="stops.txt is missing columns"):
        validate_required_columns(tables)


def test_relationships_reject_unknown_route():
    tables = {
        "trips.txt": pd.DataFrame(
            {"route_id": ["UNKNOWN"], "service_id": ["W1"], "trip_id": ["T1"]}
        ),
        "routes.txt": pd.DataFrame({"route_id": ["R1"]}),
        "calendar.txt": pd.DataFrame({"service_id": ["W1"]}),
        "stop_times.txt": pd.DataFrame(
            {"trip_id": ["T1"], "stop_id": ["S1"]}
        ),
        "stops.txt": pd.DataFrame({"stop_id": ["S1"]}),
        "calendar_dates.txt": pd.DataFrame({"service_id": ["W1"]}),
    }

    with pytest.raises(ValueError, match="trips.txt.route_id"):
        validate_relationships(tables)


def test_unique_keys_reject_duplicate_trip_id():
    tables = {
        "stops.txt": pd.DataFrame({"stop_id": ["S1"]}),
        "routes.txt": pd.DataFrame({"route_id": ["R1"]}),
        "trips.txt": pd.DataFrame(
            {
                "trip_id": ["T1", "T1"],
                "route_id": ["R1", "R1"],
                "service_id": ["W1", "W1"],
            }
        ),
        "calendar.txt": pd.DataFrame({"service_id": ["W1"]}),
        "stop_times.txt": pd.DataFrame(
            {"trip_id": ["T1"], "stop_sequence": [1]}
        ),
    }

    with pytest.raises(ValueError, match="duplicate key rows"):
        validate_unique_keys(tables)
