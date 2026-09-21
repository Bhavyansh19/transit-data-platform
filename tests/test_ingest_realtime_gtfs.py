from google.transit import gtfs_realtime_pb2

from datetime import datetime, timezone

from src.ingest_realtime_gtfs import (
    fetch_trip_updates,
    build_staging_trip_updates,
    land_raw,
    parse_trip_update_entity,
    parse_trip_updates,
)


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None


def test_fetch_trip_updates_parses_protobuf(monkeypatch, tmp_path):
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    entity = feed.entity.add()
    entity.id = "entity-1"
    entity.trip_update.trip.trip_id = "trip-123"

    response = FakeResponse(feed.SerializeToString())
    monkeypatch.setattr(
        "src.ingest_realtime_gtfs.requests.get",
        lambda *args, **kwargs: response,
    )

    entities = fetch_trip_updates("https://example.test/trip-updates")

    assert len(entities) == 1
    assert entities[0].id == "entity-1"
    assert entities[0].trip_update.trip.trip_id == "trip-123"

    parsed = parse_trip_update_entity(entities[0])

    assert parsed == {
        "entity_id": "entity-1",
        "trip_id": "trip-123",
    }

    assert parse_trip_updates(entities) == [parsed]

    output_path = land_raw(
        [parsed],
        feed_name="trip_updates",
        out_dir=tmp_path,
        captured_at=datetime(2026, 9, 20, tzinfo=timezone.utc),
    )

    assert output_path.name == "trip_updates_20260920T000000Z.json"
    assert '"trip_id": "trip-123"' in output_path.read_text()

    staging = build_staging_trip_updates(
        [parsed, parsed, {"entity_id": "entity-2", "trip_id": None}]
    )

    assert list(staging["entity_id"]) == ["entity-1"]
