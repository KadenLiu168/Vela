from __future__ import annotations

import hashlib
from copy import deepcopy

import pytest
from vela_core.walk_forward.evidence import PersistedDataContractError
from vela_core.walk_forward.provenance import (
    PROVENANCE_VERSION_V2,
    canonical_provenance_bytes,
    input_record_stream,
    sha256_hex,
    validate_input_manifest,
)


def test_configuration_provenance_uses_exact_utf8_bytes_and_excludes_source_paths() -> None:
    payload = {
        "version": "wf_provenance_v1",
        "walk_forward": {
            "strategy": {"base_config": "/tmp/strategy.yaml"},
            "parameter_space": [{"name": "x", "values": [2, 1]}],
            "label": "中文",
        },
        "base_strategy": {
            "strategy_id": "demo",
            "universe_config": "/tmp/pool.yaml",
            "parameters": {"x": 1},
        },
    }
    expected = (
        b'{"base_strategy":{"parameters":{"x":1},"strategy_id":"demo"},'
        b'"version":"wf_provenance_v1","walk_forward":{"label":"\xe4\xb8\xad\xe6\x96\x87",'
        b'"parameter_space":[{"name":"x","values":[2,1]}],"strategy":{}}}'
    )

    actual = canonical_provenance_bytes(payload)

    assert actual == expected
    assert sha256_hex(actual) == hashlib.sha256(expected).hexdigest()


def test_input_record_stream_is_tagged_ordered_and_execution_sensitive() -> None:
    records = [
        ["version", "wf_provenance_v1"],
        ["etf", 7, "SSE", "510300", "2020-01-01"],
        ["session", "2026-01-02"],
        ["following_session", None],
        ["price", 7, "SSE", "510300", "2026-01-02", "1.23", "0.99"],
    ]
    expected = (
        b'["version","wf_provenance_v1"]\n'
        b'["etf",7,"SSE","510300","2020-01-01"]\n'
        b'["session","2026-01-02"]\n'
        b'["following_session",null]\n'
        b'["price",7,"SSE","510300","2026-01-02","1.23","0.99"]\n'
    )

    actual = input_record_stream(records)

    assert actual == expected
    assert sha256_hex(actual) == hashlib.sha256(expected).hexdigest()
    assert (
        input_record_stream(
            [*records[:-1], ["price", 8, "SSE", "510300", "2026-01-02", "1.23", "0.99"]]
        )
        != actual
    )


def test_input_manifest_rejects_unreconciled_order_counts_and_date_bounds() -> None:
    manifest = {
        "version": "wf_provenance_v1",
        "earliest_required_session": "2026-01-02",
        "configured_end_date": "2026-01-05",
        "following_session": "2026-01-06",
        "official_sessions": ["2026-01-02", "2026-01-05"],
        "active_etfs": [
            {
                "etf_id": 1,
                "exchange": "SSE",
                "symbol": "510300",
                "inception_date": "2020-01-01",
                "loaded_price_row_count": 2,
                "first_loaded_price_date": "2026-01-02",
                "last_loaded_price_date": "2026-01-05",
            },
            {
                "etf_id": 2,
                "exchange": "SSE",
                "symbol": "510500",
                "inception_date": None,
                "loaded_price_row_count": 0,
                "first_loaded_price_date": None,
                "last_loaded_price_date": None,
            },
        ],
        "loaded_price_row_count": 2,
        "first_loaded_price_date": "2026-01-02",
        "last_loaded_price_date": "2026-01-05",
    }
    validate_input_manifest("wf_provenance_v1", manifest)

    corrupt_documents = []
    reversed_sessions = deepcopy(manifest)
    reversed_sessions["official_sessions"].reverse()
    corrupt_documents.append(reversed_sessions)
    reversed_etfs = deepcopy(manifest)
    reversed_etfs["active_etfs"].reverse()
    corrupt_documents.append(reversed_etfs)
    wrong_count = deepcopy(manifest)
    wrong_count["loaded_price_row_count"] = 3
    corrupt_documents.append(wrong_count)
    invalid_following = deepcopy(manifest)
    invalid_following["following_session"] = "2026-01-05"
    corrupt_documents.append(invalid_following)

    for document in corrupt_documents:
        with pytest.raises(PersistedDataContractError):
            validate_input_manifest("wf_provenance_v1", document)


def test_input_manifest_v2_reconciles_listing_status_and_derived_counts() -> None:
    manifest = {
        "version": PROVENANCE_VERSION_V2,
        "resolution_policy_version": "resolved_session_price_v1",
        "earliest_required_session": "2026-01-02",
        "configured_end_date": "2026-01-05",
        "following_session": "2026-01-06",
        "official_sessions": ["2026-01-02", "2026-01-05"],
        "active_etfs": [
            {
                "etf_id": 1,
                "exchange": "SSE",
                "symbol": "510300",
                "inception_date": "2020-01-01",
                "listing_date": "2020-01-01",
                "raw_price_row_count": 1,
                "first_raw_price_date": "2026-01-02",
                "last_raw_price_date": "2026-01-02",
                "derived_session_count": 1,
                "first_derived_session_date": "2026-01-05",
                "last_derived_session_date": "2026-01-05",
                "status_evidence": [
                    {
                        "trade_date": "2026-01-05",
                        "status": "full_day_suspension",
                        "reason": "holder_meeting",
                        "source_uri": "https://example.test/status",
                        "source_published_date": "2026-01-04",
                        "share_ratio": None,
                        "resolution": "confirmed_non_trading_carry",
                        "carried_adjusted_value": "100",
                        "carry_from_trade_date": "2026-01-02",
                    }
                ],
            }
        ],
        "raw_price_row_count": 1,
        "first_raw_price_date": "2026-01-02",
        "last_raw_price_date": "2026-01-02",
        "derived_session_count": 1,
        "first_derived_session_date": "2026-01-05",
        "last_derived_session_date": "2026-01-05",
    }

    validated = validate_input_manifest(PROVENANCE_VERSION_V2, manifest)

    assert validated.version == PROVENANCE_VERSION_V2
    assert validated.active_etfs[0].listing_date == "2020-01-01"

    corrupt = deepcopy(manifest)
    corrupt["derived_session_count"] = 2
    with pytest.raises(PersistedDataContractError):
        validate_input_manifest(PROVENANCE_VERSION_V2, corrupt)

    unsupported_policy = deepcopy(manifest)
    unsupported_policy["resolution_policy_version"] = "unknown_policy"
    with pytest.raises(PersistedDataContractError):
        validate_input_manifest(PROVENANCE_VERSION_V2, unsupported_policy)
