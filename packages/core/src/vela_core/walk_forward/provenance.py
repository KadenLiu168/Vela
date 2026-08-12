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
PROVENANCE_VERSION_V2 = "wf_provenance_v2"
STATUS_EVIDENCE_SAMPLE_LIMIT = 10


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


class StatusEvidenceManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trade_date: str
    status: Literal["full_day_suspension", "corporate_action_halt"]
    reason: str = Field(min_length=1, max_length=128)
    source_uri: str = Field(min_length=1, max_length=2048)
    source_published_date: str
    share_ratio: str | None
    resolution: Literal["confirmed_non_trading_carry"]
    carried_adjusted_value: str
    carry_from_trade_date: str

    @field_validator("trade_date", "source_published_date", "carry_from_trade_date")
    @classmethod
    def validate_dates(cls, value: str) -> str:
        date.fromisoformat(value)
        return value

    @field_validator("carried_adjusted_value")
    @classmethod
    def validate_adjusted_value(cls, value: str) -> str:
        if not value:
            raise ValueError("carried adjusted value is required")
        Decimal(value)
        return value

    @field_validator("share_ratio")
    @classmethod
    def validate_share_ratio(cls, value: str | None) -> str | None:
        if value is not None and Decimal(value) <= 0:
            raise ValueError("share ratio must be positive")
        return value


class ActiveETFManifestV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    etf_id: int
    exchange: str
    symbol: str
    inception_date: str | None
    listing_date: str
    raw_price_row_count: int = Field(ge=0)
    first_raw_price_date: str | None
    last_raw_price_date: str | None
    derived_session_count: int = Field(ge=0)
    first_derived_session_date: str | None
    last_derived_session_date: str | None
    status_evidence: list[StatusEvidenceManifestModel]

    @field_validator(
        "inception_date",
        "listing_date",
        "first_raw_price_date",
        "last_raw_price_date",
        "first_derived_session_date",
        "last_derived_session_date",
    )
    @classmethod
    def validate_dates(cls, value: str | None) -> str | None:
        if value is not None:
            date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def validate_bounds(self) -> ActiveETFManifestV2Model:
        _validate_count_bounds(
            self.raw_price_row_count,
            self.first_raw_price_date,
            self.last_raw_price_date,
            "raw price",
        )
        _validate_count_bounds(
            self.derived_session_count,
            self.first_derived_session_date,
            self.last_derived_session_date,
            "derived session",
        )
        evidence_dates = [date.fromisoformat(item.trade_date) for item in self.status_evidence]
        if evidence_dates != sorted(set(evidence_dates)):
            raise ValueError("status evidence must be unique and chronological")
        expected_evidence_count = min(self.derived_session_count, STATUS_EVIDENCE_SAMPLE_LIMIT)
        if len(evidence_dates) != expected_evidence_count:
            raise ValueError("status evidence count does not match the bounded sample")
        if evidence_dates:
            if self.first_derived_session_date != evidence_dates[0].isoformat():
                raise ValueError("derived session first bound does not match status evidence")
            if (
                self.derived_session_count <= STATUS_EVIDENCE_SAMPLE_LIMIT
                and self.last_derived_session_date != evidence_dates[-1].isoformat()
            ):
                raise ValueError("derived session last bound does not match status evidence")
        return self


class WalkForwardInputManifestV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal["wf_provenance_v2"]
    resolution_policy_version: Literal["resolved_session_price_v1"]
    earliest_required_session: str
    configured_end_date: str
    following_session: str | None
    official_sessions: list[str]
    active_etfs: list[ActiveETFManifestV2Model]
    raw_price_row_count: int = Field(ge=0)
    first_raw_price_date: str | None
    last_raw_price_date: str | None
    derived_session_count: int = Field(ge=0)
    first_derived_session_date: str | None
    last_derived_session_date: str | None

    @field_validator(
        "earliest_required_session",
        "configured_end_date",
        "following_session",
        "official_sessions",
        "first_raw_price_date",
        "last_raw_price_date",
        "first_derived_session_date",
        "last_derived_session_date",
        mode="before",
    )
    @classmethod
    def validate_dates(cls, value: Any) -> Any:
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item is not None:
                date.fromisoformat(item)
        return value

    @model_validator(mode="after")
    def validate_manifest_reconciliation(self) -> WalkForwardInputManifestV2Model:
        official_dates = [date.fromisoformat(value) for value in self.official_sessions]
        if not official_dates or official_dates != sorted(set(official_dates)):
            raise ValueError("official sessions must be unique and chronological")
        earliest = date.fromisoformat(self.earliest_required_session)
        configured_end = date.fromisoformat(self.configured_end_date)
        if earliest != official_dates[0] or official_dates[-1] > configured_end:
            raise ValueError("official session bounds do not match the manifest envelope")
        if self.following_session is not None and date.fromisoformat(self.following_session) <= (
            configured_end
        ):
            raise ValueError("following session must be after configured end date")
        ids = [item.etf_id for item in self.active_etfs]
        if ids != sorted(set(ids)):
            raise ValueError("active ETFs must be unique and ordered by local id")
        if self.raw_price_row_count != sum(item.raw_price_row_count for item in self.active_etfs):
            raise ValueError("global raw price count must equal per-ETF counts")
        if self.derived_session_count != sum(
            item.derived_session_count for item in self.active_etfs
        ):
            raise ValueError("global derived count must equal per-ETF counts")
        _validate_count_bounds(
            self.raw_price_row_count,
            self.first_raw_price_date,
            self.last_raw_price_date,
            "global raw price",
        )
        _validate_count_bounds(
            self.derived_session_count,
            self.first_derived_session_date,
            self.last_derived_session_date,
            "global derived session",
        )
        self._validate_global_bounds("raw_price", "raw price")
        self._validate_global_bounds("derived_session", "derived session")
        for value in (
            self.first_raw_price_date,
            self.last_raw_price_date,
            self.first_derived_session_date,
            self.last_derived_session_date,
        ):
            if value is not None:
                boundary = date.fromisoformat(value)
                if boundary < earliest or boundary > configured_end:
                    raise ValueError("manifest source bounds exceed the configured envelope")
        for etf in self.active_etfs:
            listing = date.fromisoformat(etf.listing_date)
            for value in (etf.first_raw_price_date, etf.last_raw_price_date):
                if value is not None and date.fromisoformat(value) < listing:
                    raise ValueError("raw prices must not precede ETF listing")
            for value in (etf.first_derived_session_date, etf.last_derived_session_date):
                if value is not None and date.fromisoformat(value) < listing:
                    raise ValueError("derived sessions must not precede ETF listing")
            for evidence in etf.status_evidence:
                status_date = date.fromisoformat(evidence.trade_date)
                carry_date = date.fromisoformat(evidence.carry_from_trade_date)
                if status_date not in official_dates or status_date < listing:
                    raise ValueError("status evidence must be on a listed official session")
                if carry_date >= status_date:
                    raise ValueError("status evidence carry ancestry must precede the session")
                status_index = official_dates.index(status_date)
                if status_index > 0 and carry_date != official_dates[status_index - 1]:
                    raise ValueError("status evidence must carry the preceding official session")
            evidence_by_date = {
                date.fromisoformat(evidence.trade_date): evidence
                for evidence in etf.status_evidence
            }
            for evidence in etf.status_evidence:
                ancestor = evidence_by_date.get(date.fromisoformat(evidence.carry_from_trade_date))
                if (
                    ancestor is not None
                    and ancestor.carried_adjusted_value != evidence.carried_adjusted_value
                ):
                    raise ValueError("consecutive status evidence must carry an unchanged value")
        return self

    def _validate_global_bounds(self, prefix: str, label: str) -> None:
        first_values = [
            getattr(item, f"first_{prefix}_date")
            for item in self.active_etfs
            if getattr(item, f"first_{prefix}_date") is not None
        ]
        last_values = [
            getattr(item, f"last_{prefix}_date")
            for item in self.active_etfs
            if getattr(item, f"last_{prefix}_date") is not None
        ]
        if getattr(self, f"first_{prefix}_date") != min(first_values, default=None):
            raise ValueError(f"global {label} first bound does not reconcile")
        if getattr(self, f"last_{prefix}_date") != max(last_values, default=None):
            raise ValueError(f"global {label} last bound does not reconcile")


def validate_input_manifest(
    version: str, document: object
) -> WalkForwardInputManifestModel | WalkForwardInputManifestV2Model:
    if version == PROVENANCE_VERSION_V2:
        try:
            manifest = WalkForwardInputManifestV2Model.model_validate(document)
            if manifest.version != PROVENANCE_VERSION_V2:
                raise ValueError("manifest version does not match parent provenance version")
            return manifest
        except Exception as exc:
            if isinstance(exc, PersistedDataContractError):
                raise
            raise PersistedDataContractError(
                "invalid persisted Walk-forward input manifest"
            ) from exc
    if version != PROVENANCE_VERSION:
        raise PersistedDataContractError(f"unsupported Walk-forward provenance version: {version}")
    try:
        legacy_manifest = WalkForwardInputManifestModel.model_validate(document)
        if legacy_manifest.version != PROVENANCE_VERSION:
            raise ValueError("manifest version does not match parent provenance version")
        return legacy_manifest
    except Exception as exc:
        if isinstance(exc, PersistedDataContractError):
            raise
        raise PersistedDataContractError("invalid persisted Walk-forward input manifest") from exc


def canonical_provenance_payload(
    walk_forward: dict[str, Any],
    base_strategy: dict[str, Any],
    *,
    version: str = PROVENANCE_VERSION,
    resolution_policy_version: str | None = None,
) -> dict[str, Any]:
    walk_forward_snapshot = copy.deepcopy(walk_forward)
    strategy = walk_forward_snapshot.get("strategy")
    if isinstance(strategy, dict):
        strategy.pop("base_config", None)
    base_strategy_snapshot = copy.deepcopy(base_strategy)
    base_strategy_snapshot.pop("universe_config", None)
    payload: dict[str, Any] = {
        "version": version,
        "walk_forward": walk_forward_snapshot,
        "base_strategy": base_strategy_snapshot,
    }
    if resolution_policy_version is not None:
        payload["resolution_policy_version"] = resolution_policy_version
    return payload


def canonical_provenance_bytes(payload: dict[str, Any]) -> bytes:
    normalized = canonical_provenance_payload(
        payload["walk_forward"],
        payload["base_strategy"],
        version=payload.get("version", PROVENANCE_VERSION),
        resolution_policy_version=payload.get("resolution_policy_version"),
    )
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


def _validate_count_bounds(
    count: int, first_value: str | None, last_value: str | None, label: str
) -> None:
    if count == 0 and (first_value is not None or last_value is not None):
        raise ValueError(f"zero-row {label} must contain null bounds")
    if count > 0 and (first_value is None or last_value is None):
        raise ValueError(f"non-empty {label} must contain both bounds")
    if (
        first_value is not None
        and last_value is not None
        and date.fromisoformat(first_value) > date.fromisoformat(last_value)
    ):
        raise ValueError(f"{label} bounds must be chronological")
