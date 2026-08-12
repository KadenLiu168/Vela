from vela_api.schemas import WalkForwardInputProvenanceResponse


def test_input_provenance_schema_accepts_discriminated_v1_and_v2_manifests() -> None:
    v1 = WalkForwardInputProvenanceResponse.model_validate(
        {
            "manifest": {
                "version": "wf_provenance_v1",
                "earliest_required_session": "2026-01-02",
                "configured_end_date": "2026-01-05",
                "following_session": None,
                "official_sessions": ["2026-01-02"],
                "active_etfs": [],
                "loaded_price_row_count": 0,
                "first_loaded_price_date": None,
                "last_loaded_price_date": None,
            },
            "input_data_checksum": "a" * 64,
        }
    )
    v2 = WalkForwardInputProvenanceResponse.model_validate(
        {
            "manifest": {
                "version": "wf_provenance_v2",
                "resolution_policy_version": "resolved_session_price_v1",
                "earliest_required_session": "2026-01-02",
                "configured_end_date": "2026-01-05",
                "following_session": None,
                "official_sessions": ["2026-01-02"],
                "active_etfs": [],
                "raw_price_row_count": 0,
                "first_raw_price_date": None,
                "last_raw_price_date": None,
                "derived_session_count": 0,
                "first_derived_session_date": None,
                "last_derived_session_date": None,
            },
            "input_data_checksum": "b" * 64,
        }
    )

    assert v1.manifest.version == "wf_provenance_v1"
    assert v2.manifest.version == "wf_provenance_v2"
    schema = WalkForwardInputProvenanceResponse.model_json_schema()
    manifest_schema = schema["properties"]["manifest"]
    assert "discriminator" in manifest_schema
    assert manifest_schema["discriminator"]["propertyName"] == "version"
