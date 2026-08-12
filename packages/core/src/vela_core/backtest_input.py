from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from typing import TypeAlias, cast

from vela_core.models import ETFInfo, MarketPrice
from vela_core.resolved_session_price import ResolvedSessionPrice

BACKTEST_INPUT_VERSION = "backtest_input_v2"
_SUPPORTED_STATUSES = {"full_day_suspension", "corporate_action_halt"}
_SessionPrice: TypeAlias = MarketPrice | ResolvedSessionPrice


def build_backtest_input_v2(
    *,
    active_etfs: Sequence[ETFInfo],
    official_sessions: Sequence[date],
    following_session: date | None,
    price_panel: Mapping[int, Sequence[_SessionPrice]],
) -> dict[str, object]:
    sessions = list(official_sessions)
    etfs = sorted(active_etfs, key=lambda item: item.id or 0)
    raw_records: list[dict[str, object]] = []
    derived_sessions: list[dict[str, object]] = []
    identity = {etf.id: etf for etf in etfs}
    for etf in etfs:
        for price in price_panel.get(etf.id, ()):
            if etf.listing_date is None:
                raise ValueError(f"backtest_input_v2 requires listing_date for ETF {etf.id}")
            if price.trade_date not in sessions or price.trade_date < etf.listing_date:
                continue
            if isinstance(price, ResolvedSessionPrice):
                if price.resolution == "market_price":
                    if price.raw_close is None or price.raw_factor is None:
                        raise ValueError("market-price resolution requires raw values")
                    raw_records.append(_raw_record(price, etf.exchange, etf.symbol))
                else:
                    derived_sessions.append(_derived_record(price, etf.exchange, etf.symbol))
            else:
                raw_records.append(
                    {
                        "etf_id": price.etf_id,
                        "exchange": etf.exchange,
                        "symbol": etf.symbol,
                        "trade_date": price.trade_date.isoformat(),
                        "close_price": str(price.close_price),
                        "factor_hfq": str(price.factor_hfq),
                    }
                )
    raw_records.sort(key=lambda item: (_record_id(item), str(item["trade_date"])))
    derived_sessions.sort(key=lambda item: (_record_id(item), str(item["trade_date"])))
    active_manifest = [
        {
            "etf_id": etf.id,
            "exchange": etf.exchange,
            "symbol": etf.symbol,
            "inception_date": _iso(etf.inception_date),
            "listing_date": _iso(etf.listing_date),
        }
        for etf in etfs
    ]
    raw_counts = _counts(raw_records)
    derived_counts = _counts(derived_sessions)
    raw_per_etf = cast(dict[str, int], raw_counts["per_etf"])
    derived_per_etf = cast(dict[str, int], derived_counts["per_etf"])
    raw_bounds = _bounds(raw_records)
    derived_bounds = _bounds(derived_sessions)
    document: dict[str, object] = {
        "version": BACKTEST_INPUT_VERSION,
        "resolution_policy_version": "resolved_session_price_v1",
        "official_sessions": [item.isoformat() for item in sessions],
        "following_session": _iso(following_session),
        "active_etfs": active_manifest,
        "raw_price_records": raw_records,
        "derived_sessions": derived_sessions,
        "raw_price_counts": raw_counts,
        "derived_session_counts": derived_counts,
        "raw_price_bounds": raw_bounds,
        "derived_session_bounds": derived_bounds,
        "min_trade_date": _min_bound(raw_bounds, derived_bounds),
        "max_trade_date": _max_bound(raw_bounds, derived_bounds),
        "trading_day_count": len(sessions),
        "active_etf_count": len(etfs),
        "per_etf_row_counts": {
            str(etf_id): raw_per_etf.get(str(etf_id), 0) + derived_per_etf.get(str(etf_id), 0)
            for etf_id in identity
        },
    }
    document["data_checksum"] = _checksum(document)
    validate_backtest_input_v2(document)
    return document


def validate_backtest_input_v2(document: object) -> dict[str, object]:
    if not isinstance(document, dict) or document.get("version") != BACKTEST_INPUT_VERSION:
        raise ValueError("invalid backtest_input_v2 version")
    if document.get("resolution_policy_version") != "resolved_session_price_v1":
        raise ValueError("backtest_input_v2 resolution policy is unsupported")
    sessions = _parse_dates(document.get("official_sessions"), "official_sessions")
    if not sessions or sessions != sorted(set(sessions)):
        raise ValueError("backtest_input_v2 official sessions must be unique and chronological")
    _validate_following_session(document.get("following_session"), sessions[-1])
    etfs = document.get("active_etfs")
    if not isinstance(etfs, list):
        raise ValueError("backtest_input_v2 active_etfs must be a list")
    identities: dict[int, dict[str, object]] = {}
    ids: list[int] = []
    for item in etfs:
        if not isinstance(item, dict):
            raise ValueError("backtest_input_v2 ETF metadata must be an object")
        etf_id = _positive_int(item.get("etf_id"), "etf_id")
        if etf_id in identities:
            raise ValueError("backtest_input_v2 ETF ids must be unique")
        _require_text(item.get("exchange"), "exchange")
        _require_text(item.get("symbol"), "symbol")
        listing = _parse_optional_date(item.get("listing_date"), "listing_date")
        _parse_optional_date(item.get("inception_date"), "inception_date")
        if listing is None:
            raise ValueError("backtest_input_v2 requires listing_date")
        identities[etf_id] = item
        ids.append(etf_id)
    if ids != sorted(ids):
        raise ValueError("backtest_input_v2 ETF metadata must be ordered by local id")

    raw_records = _records(document, "raw_price_records")
    derived_sessions = _records(document, "derived_sessions")
    raw_values = _validate_raw_records(raw_records, identities, sessions)
    raw_keys = set(raw_values)
    derived_keys = _validate_derived_records(derived_sessions, identities, sessions, raw_values)
    if raw_keys & derived_keys:
        raise ValueError("backtest_input_v2 raw and derived records must be source-exclusive")
    if document.get("raw_price_counts") != _counts(raw_records):
        raise ValueError("backtest_input_v2 raw counts do not reconcile")
    if document.get("derived_session_counts") != _counts(derived_sessions):
        raise ValueError("backtest_input_v2 derived counts do not reconcile")
    if document.get("raw_price_bounds") != _bounds(raw_records):
        raise ValueError("backtest_input_v2 raw bounds do not reconcile")
    if document.get("derived_session_bounds") != _bounds(derived_sessions):
        raise ValueError("backtest_input_v2 derived bounds do not reconcile")
    expected_keys = {
        (etf_id, trade_date)
        for etf_id, item in identities.items()
        for trade_date in sessions
        if trade_date >= _parse_date(item["listing_date"], "listing_date")
    }
    if raw_keys | derived_keys != expected_keys:
        raise ValueError("backtest_input_v2 requires one complete source state per listed session")
    raw_counts = cast(dict[str, int], _counts(raw_records)["per_etf"])
    derived_counts = cast(dict[str, int], _counts(derived_sessions)["per_etf"])
    expected_per_etf = {
        str(etf_id): raw_counts.get(str(etf_id), 0) + derived_counts.get(str(etf_id), 0)
        for etf_id in identities
    }
    if document.get("per_etf_row_counts") != expected_per_etf:
        raise ValueError("backtest_input_v2 per-ETF row counts do not reconcile")
    if document.get("trading_day_count") != len(sessions):
        raise ValueError("backtest_input_v2 trading day count does not reconcile")
    if document.get("active_etf_count") != len(identities):
        raise ValueError("backtest_input_v2 active ETF count does not reconcile")
    raw_bounds = _bounds(raw_records)
    derived_bounds = _bounds(derived_sessions)
    if document.get("min_trade_date") != _min_bound(raw_bounds, derived_bounds):
        raise ValueError("backtest_input_v2 minimum trade date does not reconcile")
    if document.get("max_trade_date") != _max_bound(raw_bounds, derived_bounds):
        raise ValueError("backtest_input_v2 maximum trade date does not reconcile")
    expected_checksum = _checksum(document)
    if document.get("data_checksum") != expected_checksum:
        raise ValueError("backtest_input_v2 checksum does not reconcile")
    return document


def _raw_record(price: ResolvedSessionPrice, exchange: str, symbol: str) -> dict[str, object]:
    assert price.raw_close is not None
    assert price.raw_factor is not None
    return {
        "etf_id": price.etf_id,
        "exchange": exchange,
        "symbol": symbol,
        "trade_date": price.trade_date.isoformat(),
        "close_price": str(price.raw_close),
        "factor_hfq": str(price.raw_factor),
    }


def _derived_record(price: ResolvedSessionPrice, exchange: str, symbol: str) -> dict[str, object]:
    if (
        price.status not in _SUPPORTED_STATUSES
        or not price.reason
        or not price.source_uri
        or price.source_published_date is None
        or price.carry_from_trade_date is None
    ):
        raise ValueError("derived session requires supported status evidence and carry ancestry")
    return {
        "etf_id": price.etf_id,
        "exchange": exchange,
        "symbol": symbol,
        "trade_date": price.trade_date.isoformat(),
        "status": price.status,
        "reason": price.reason,
        "source_uri": price.source_uri,
        "source_published_date": price.source_published_date.isoformat(),
        "share_ratio": _decimal_or_none(price.share_ratio),
        "resolution": price.resolution,
        "carried_adjusted_value": str(price.adjusted_value),
        "carry_from_trade_date": price.carry_from_trade_date.isoformat(),
    }


def _validate_raw_records(
    records: list[dict[str, object]], identities: dict[int, dict[str, object]], sessions: list[date]
) -> dict[tuple[int, date], Decimal]:
    values: dict[tuple[int, date], Decimal] = {}
    previous: tuple[int, date] | None = None
    for record in records:
        key = _record_key(record, identities, sessions)
        if previous is not None and key < previous:
            raise ValueError("backtest_input_v2 raw records must be ordered")
        if key in values:
            raise ValueError("backtest_input_v2 raw records must be unique")
        values[key] = _decimal(record.get("close_price"), "close_price") * _decimal(
            record.get("factor_hfq"), "factor_hfq"
        )
        previous = key
    return values


def _validate_derived_records(
    records: list[dict[str, object]],
    identities: dict[int, dict[str, object]],
    sessions: list[date],
    raw_values: dict[tuple[int, date], Decimal],
) -> set[tuple[int, date]]:
    keys: set[tuple[int, date]] = set()
    adjusted_values = dict(raw_values)
    raw_keys = set(raw_values)
    previous: tuple[int, date] | None = None
    for record in records:
        key = _record_key(record, identities, sessions)
        if previous is not None and key < previous:
            raise ValueError("backtest_input_v2 derived records must be ordered")
        if key in keys or key in raw_keys:
            raise ValueError("backtest_input_v2 derived records must be source-exclusive")
        if record.get("status") not in _SUPPORTED_STATUSES:
            raise ValueError("backtest_input_v2 derived status is unsupported")
        for field in ("reason", "source_uri", "source_published_date", "resolution"):
            _require_text(record.get(field), field)
        if record.get("resolution") != "confirmed_non_trading_carry":
            raise ValueError("backtest_input_v2 derived resolution is invalid")
        carried_value = _decimal(record.get("carried_adjusted_value"), "carried_adjusted_value")
        carry_date = _parse_date(record.get("carry_from_trade_date"), "carry_from_trade_date")
        carry_key = (key[0], carry_date)
        if carry_date >= key[1] or carry_key not in adjusted_values:
            raise ValueError("backtest_input_v2 carry ancestry does not reconcile")
        if carried_value != adjusted_values[carry_key]:
            raise ValueError("backtest_input_v2 carried adjusted value does not match ancestry")
        ratio = record.get("share_ratio")
        if ratio is not None and Decimal(str(ratio)) <= 0:
            raise ValueError("backtest_input_v2 share ratio must be positive")
        keys.add(key)
        adjusted_values[key] = carried_value
        previous = key
    return keys


def _record_key(
    record: dict[str, object], identities: dict[int, dict[str, object]], sessions: list[date]
) -> tuple[int, date]:
    etf_id = _positive_int(record.get("etf_id"), "etf_id")
    if etf_id not in identities:
        raise ValueError("backtest_input_v2 record references unknown ETF")
    trade_date = _parse_date(record.get("trade_date"), "trade_date")
    if trade_date not in sessions:
        raise ValueError("backtest_input_v2 record is outside official sessions")
    listing = _parse_date(identities[etf_id]["listing_date"], "listing_date")
    if trade_date < listing:
        raise ValueError("backtest_input_v2 record precedes ETF listing")
    if record.get("exchange") != identities[etf_id].get("exchange") or record.get(
        "symbol"
    ) != identities[etf_id].get("symbol"):
        raise ValueError("backtest_input_v2 record identity does not reconcile")
    return etf_id, trade_date


def _record_id(record: dict[str, object]) -> int:
    value = record.get("etf_id")
    if not isinstance(value, int):
        raise ValueError("backtest_input_v2 record ETF id must be an integer")
    return value


def _checksum(document: dict[str, object]) -> str:
    active_etfs = cast(list[dict[str, object]], document["active_etfs"])
    official_sessions = cast(list[str], document["official_sessions"])
    raw_price_records = cast(list[dict[str, object]], document["raw_price_records"])
    derived_sessions = cast(list[dict[str, object]], document["derived_sessions"])
    records: list[list[object]] = [["version", document["version"]]]
    records.append(["policy", document["resolution_policy_version"]])
    records.extend(
        [
            "etf",
            item["etf_id"],
            item["exchange"],
            item["symbol"],
            item["inception_date"],
            item["listing_date"],
        ]
        for item in active_etfs
    )
    records.extend(["session", value] for value in official_sessions)
    records.append(["following_session", document["following_session"]])
    records.extend(
        [
            "raw",
            item["etf_id"],
            item["exchange"],
            item["symbol"],
            item["trade_date"],
            item["close_price"],
            item["factor_hfq"],
        ]
        for item in raw_price_records
    )
    records.extend(
        [
            "derived",
            item["etf_id"],
            item["exchange"],
            item["symbol"],
            item["trade_date"],
            item["status"],
            item["reason"],
            item["source_uri"],
            item["source_published_date"],
            item["share_ratio"],
            item["resolution"],
            item["carried_adjusted_value"],
            item["carry_from_trade_date"],
        ]
        for item in derived_sessions
    )
    payload = b"".join(_json_bytes(record) + b"\n" for record in records)
    return hashlib.sha256(payload).hexdigest()


def _counts(records: list[dict[str, object]]) -> dict[str, object]:
    per_etf: dict[str, int] = {}
    for record in records:
        key = str(record["etf_id"])
        per_etf[key] = per_etf.get(key, 0) + 1
    return {"global": len(records), "per_etf": per_etf}


def _bounds(records: list[dict[str, object]]) -> dict[str, str | None]:
    values = [str(record["trade_date"]) for record in records]
    return {"first": min(values) if values else None, "last": max(values) if values else None}


def _records(document: dict[str, object], field: str) -> list[dict[str, object]]:
    value = document.get(field)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"backtest_input_v2 {field} must be a list of objects")
    return value  # type: ignore[return-value]


def _parse_dates(value: object, field: str) -> list[date]:
    if not isinstance(value, list):
        raise ValueError(f"backtest_input_v2 {field} must be a list")
    return [_parse_date(item, field) for item in value]


def _parse_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"backtest_input_v2 {field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"backtest_input_v2 {field} must be an ISO date") from exc


def _parse_optional_date(value: object, field: str) -> date | None:
    return None if value is None else _parse_date(value, field)


def _validate_following_session(value: object, last_session: date) -> None:
    if value is not None and _parse_date(value, "following_session") <= last_session:
        raise ValueError("backtest_input_v2 following session must be after official sessions")


def _positive_int(value: object, field: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"backtest_input_v2 {field} must be positive")
    return value


def _require_text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"backtest_input_v2 {field} is required")


def _decimal(value: object, field: str) -> Decimal:
    _require_text(value, field)
    parsed = Decimal(str(value))
    if not parsed.is_finite():
        raise ValueError(f"backtest_input_v2 {field} must be finite")
    return parsed


def _decimal_or_none(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _iso(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _min_bound(*bounds: dict[str, str | None]) -> str | None:
    values = [item["first"] for item in bounds if item["first"] is not None]
    return min(values) if values else None


def _max_bound(*bounds: dict[str, str | None]) -> str | None:
    values = [item["last"] for item in bounds if item["last"] is not None]
    return max(values) if values else None


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
