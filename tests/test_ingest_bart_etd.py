from datetime import datetime, timezone

from src.ingest_bart_etd import land_etd, parse_etd_response
from src.load_bart_etd_to_postgres import read_etd_snapshot


def sample_payload():
    return {
        "root": {
            "station": [
                {
                    "name": "Downtown Berkeley",
                    "abbr": "DBRK",
                    "etd": [
                        {
                            "destination": "Berryessa",
                            "abbreviation": "BERY",
                            "estimate": [
                                {
                                    "minutes": "5",
                                    "platform": "2",
                                    "direction": "South",
                                    "length": "6",
                                    "color": "GREEN",
                                    "delay": "0",
                                    "cancelflag": "0",
                                    "dynamicflag": "0",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
    }


def test_parse_etd_response_flattens_nested_json():
    assert parse_etd_response(sample_payload()) == [
        {
            "station_abbr": "DBRK",
            "station_name": "Downtown Berkeley",
            "destination_abbr": "BERY",
            "destination_name": "Berryessa",
            "minutes": "5",
            "platform": "2",
            "direction": "South",
            "train_length": "6",
            "color": "GREEN",
            "delay_seconds": "0",
            "cancelled": "0",
            "dynamic": "0",
        }
    ]


def test_land_etd_is_idempotent_and_loadable(tmp_path):
    captured_at = datetime(2026, 11, 17, tzinfo=timezone.utc)
    first = land_etd(sample_payload(), "https://example.test/etd", tmp_path, captured_at)
    second = land_etd(sample_payload(), "https://example.test/etd", tmp_path, captured_at)

    assert first == second
    assert len(list(tmp_path.glob("etd_*.json"))) == 1
    assert read_etd_snapshot(first)[0][2:7] == (
        "DBRK",
        "Downtown Berkeley",
        "BERY",
        "Berryessa",
        "5",
    )
