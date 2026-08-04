from __future__ import annotations

import copy
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from vela_core.walk_forward.evidence import PersistedDataContractError

PROVENANCE_VERSION = "wf_provenance_v1"


class ActiveETFManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    etf_id: int
    exchange: str
    symbol: str
    inception_date: str | None
    loaded_price_row_count: int = Field(ge=0)
    first_loaded_price_date: str | None
    last_loaded_price_date: str | None

    @field_validator("inception_date", "first_loaded_price_date", "last_loaded_price_date")
    @classmethod
    def validate_iso_dates(cls, value: str | None) -> str | None:
        if value is not None:
            date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def validate_loaded_price_bounds(self) -> ActiveETFManifestModel:
        first = _date_value(self.first_loaded_price_date)
        last = _date_value(self.last_loaded_price_date)
        inception = _date_value(self.inception_date)
        if self.loaded_price_row_count == 0 and (first is not None or last is not None):
            raise ValueError("zero-row ETF manifest must contain null price bounds")
        if self.loaded_price_row_count > 0 and (first is None or last is None):
            raise ValueError("non-empty ETF manifest must contain both price bounds")
        if first is not None and last is not None and first > last:
            raise ValueError("ETF price bounds must be chronological")
        if inception is not None and first is not None and first < inception:
            raise ValueError("ETF loaded prices must not precede inception")
        return self


class WalkForwardInputManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["wf_provenance_v1"]
    earliest_required_session: str
    configured_end_date: str
    following_session: str | None
    official_sessions: list[str]
    active_etfs: list[ActiveETFManifestModel]
    loaded_price_row_count: int = Field(ge=0)
    first_loaded_price_date: str | None
    last_loaded_price_date: str | None

    @field_validator(
        "earliest_required_session",
        "configured_end_date",
        "following_session",
        "official_sessions",
        "first_loaded_price_date",
        "last_loaded_price_date",
        mode="before",
    )
    @classmethod
    def validate_iso_dates(cls, value: Any) -> Any:
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item is not None:
                date.fromisoformat(item)
        return value

    @model_validator(mode="after")
    def validate_manifest_reconciliation(self) -> WalkForwardInputManifestModel:
        official_dates = [_date_value(value) for value in self.official_sessions]
        if not official_dates or any(value is None for value in official_dates):
            raise ValueError("manifest requires at least one official session")
        ordered_dates = [value for value in official_dates if value is not None]
        if ordered_dates != sorted(set(ordered_dates)):
            raise ValueError("official sessions must be unique and chronological")

        earliest = _date_value(self.earliest_required_session)
        configured_end = _date_value(self.configured_end_date)
        following = _date_value(self.following_session)
        assert earliest is not None
        assert configured_end is not None
        if earliest != ordered_dates[0] or ordered_dates[-1] > configured_end:
            raise ValueError("official session bounds do not match the manifest envelope")
        if following is not None and following <= configured_end:
            raise ValueError("following session must be after the configured end date")

        etf_ids = [item.etf_id for item in self.active_etfs]
        if etf_ids != sorted(set(etf_ids)):
            raise ValueError("active ETFs must be unique and ordered by local id")
        if self.loaded_price_row_count != sum(
            item.loaded_price_row_count for item in self.active_etfs
        ):
            raise ValueError("global loaded price count must equal the per-ETF counts")

        first_dates = [
            value
            for item in self.active_etfs
            if (value := _date_value(item.first_loaded_price_date)) is not None
        ]
        last_dates = [
            value
            for item in self.active_etfs
            if (value := _date_value(item.last_loaded_price_date)) is not None
        ]
        expected_first = min(first_dates, default=None)
        expected_last = max(last_dates, default=None)
        if (
            _date_value(self.first_loaded_price_date) != expected_first
            or _date_value(self.last_loaded_price_date) != expected_last
        ):
            raise ValueError("global loaded price bounds must match the per-ETF bounds")
        if expected_first is not None and expected_first < earliest:
            raise ValueError("loaded prices must not precede the required envelope")
        if expected_last is not None and expected_last > configured_end:
            raise ValueError("loaded prices must not follow the configured end date")
        return self


def validate_input_manifest(version: str, document: object) -> WalkForwardInputManifestModel:
    if version != PROVENANCE_VERSION:
        raise PersistedDataContractError(f"unsupported Walk-forward provenance version: {version}")
    try:
        manifest = WalkForwardInputManifestModel.model_validate(document)
        if manifest.version != PROVENANCE_VERSION:
            raise ValueError("manifest version does not match parent provenance version")
        return manifest
    except Exception as exc:
        if isinstance(exc, PersistedDataContractError):
            raise
        raise PersistedDataContractError("invalid persisted Walk-forward input manifest") from exc


def canonical_provenance_payload(
    walk_forward: dict[str, Any], base_strategy: dict[str, Any]
) -> dict[str, Any]:
    walk_forward_snapshot = copy.deepcopy(walk_forward)
    strategy = walk_forward_snapshot.get("strategy")
    if isinstance(strategy, dict):
        strategy.pop("base_config", None)
    base_strategy_snapshot = copy.deepcopy(base_strategy)
    base_strategy_snapshot.pop("universe_config", None)
    return {
        "version": PROVENANCE_VERSION,
        "walk_forward": walk_forward_snapshot,
        "base_strategy": base_strategy_snapshot,
    }


def canonical_provenance_bytes(payload: dict[str, Any]) -> bytes:
    normalized = canonical_provenance_payload(payload["walk_forward"], payload["base_strategy"])
    return _json_bytes(normalized)


def input_record_stream(records: list[list[Any]]) -> bytes:
    return b"".join(_json_bytes(record) + b"\n" for record in records)


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=_json_default,
    ).encode("utf-8")


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _date_value(value: str | None) -> date | None:
    return None if value is None else date.fromisoformat(value)
