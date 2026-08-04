from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vela_core.backtest_runner import run_backtest
from vela_core.models import MarketPrice, TradingCalendar
from vela_core.walk_forward.config import WalkForwardConfig
from vela_core.walk_forward.parameter_space import (
    build_strategy_config,
    canonical_combination,
    generate_combinations,
)
from vela_core.walk_forward.report import (
    WalkForwardBenchmarkResult,
    WalkForwardReport,
    WalkForwardWindowResult,
)
from vela_core.walk_forward.window_splitter import WalkForwardWindow, generate_windows

logger = logging.getLogger(__name__)


class WalkForwardRunner:
    def __init__(self, config: WalkForwardConfig) -> None:
        self.config = config
        self._base_config = _load_base_config(config.strategy.base_config)
        self._version_contents: dict[str, str] = {}

    def run(self, session: Session) -> WalkForwardReport:
        if session.get_bind().dialect.name != "sqlite":
            raise ValueError("walk-forward only supports SQLite source databases")
        dates = list(
            session.scalars(
                select(MarketPrice.trade_date)
                .where(MarketPrice.trade_date >= self.config.window.start_date)
                .where(MarketPrice.trade_date <= self.config.window.end_date)
                .distinct()
                .order_by(MarketPrice.trade_date)
            )
        )
        if not dates:
            dates = list(
                session.scalars(
                    select(TradingCalendar.trade_date)
                    .where(TradingCalendar.trade_date >= self.config.window.start_date)
                    .where(TradingCalendar.trade_date <= self.config.window.end_date)
                    .order_by(TradingCalendar.trade_date)
                )
            )
        window_config = self.config.window
        windows = generate_windows(
            dates,
            window_config.start_date,
            window_config.end_date,
            window_config.train_years,
            window_config.test_years,
            window_config.step_years,
        )
        combinations = generate_combinations(self.config.parameter_space)
        with _memory_snapshot(session) as memory:
            results = [self._run_window(session, memory, item, combinations) for item in windows]
        return WalkForwardReport(results)

    def _run_window(
        self,
        source: Session,
        memory: Session,
        window: WalkForwardWindow,
        combinations: list[dict[str, Any]],
    ) -> WalkForwardWindowResult:
        scored: list[tuple[float, str, dict[str, Any], Any]] = []
        skipped: list[str] = []
        for combo in combinations:
            built = build_strategy_config(self._base_config, combo)
            if built.config is None:
                memory.rollback()
                reason = f"{canonical_combination(combo)}: {built.skip_reason}"
                logger.warning("Walk-forward skipped combination %s", reason)
                skipped.append(reason)
                continue
            try:
                result = run_backtest(
                    memory,
                    config=built.config,
                    start_date=window.train_start,
                    end_date=window.train_end,
                    calculate_benchmarks=False,
                )
                if result.status == "success" and result.sharpe_ratio is not None:
                    scored.append(
                        (
                            float(result.sharpe_ratio),
                            canonical_combination(combo),
                            combo,
                            built.config,
                        )
                    )
                    memory.commit()
                else:
                    memory.rollback()
                    reason = f"{canonical_combination(combo)}: unscorable result"
                    logger.warning("Walk-forward skipped combination %s", reason)
                    skipped.append(reason)
            except Exception as exc:
                memory.rollback()
                reason = f"{canonical_combination(combo)}: {exc}"
                logger.warning("Walk-forward skipped combination %s", reason)
                skipped.append(reason)
        if not scored:
            raise RuntimeError("no scorable parameter combinations before OOS evaluation")
        best = min(scored, key=lambda item: (-item[0], item[1]))
        validated_data = best[3].model_dump(mode="json")
        selected_parameters = _validated_combination(validated_data, best[2])
        version = _version_for_config(validated_data)
        content = _canonical_config_content(validated_data)
        if self._version_contents.get(version) not in (None, content):
            raise RuntimeError(f"walk-forward version collision for {version}")
        self._version_contents[version] = content
        oos_config = best[3].model_copy(update={"version": version})
        oos = run_backtest(
            source,
            config=oos_config,
            start_date=window.test_start,
            end_date=window.test_end,
            calculate_benchmarks=True,
        )
        if oos.status != "success":
            raise RuntimeError(f"OOS backtest returned {oos.status}")
        return WalkForwardWindowResult(
            window=window,
            best_combo=selected_parameters,
            oos_version=version,
            train_sharpe=best[0],
            oos_total_return=_number(oos.total_return),
            oos_annualized_return=_number(oos.annualized_return),
            oos_sharpe=_number(oos.sharpe_ratio),
            oos_max_drawdown=_number(oos.max_drawdown),
            oos_volatility=_number(oos.volatility),
            benchmarks=tuple(
                WalkForwardBenchmarkResult(
                    key=item.key,
                    name=item.name,
                    total_return=_number(item.annualized_return.total_return),
                    annualized_return=_number(item.annualized_return.annualized_return),
                    max_drawdown=_number(item.maximum_drawdown.max_drawdown),
                    volatility=_number(item.volatility.volatility),
                    sharpe_ratio=_number(item.sharpe_ratio.sharpe_ratio),
                    total_return_difference=_difference(
                        oos.total_return, item.annualized_return.total_return
                    ),
                    annualized_return_difference=_difference(
                        oos.annualized_return, item.annualized_return.annualized_return
                    ),
                )
                for item in getattr(oos, "benchmarks", ())
            ),
            skipped=skipped,
        )


def _load_base_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"base strategy configuration {path} must be a mapping")
    return data


@contextmanager
def _memory_snapshot(source: Session) -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", poolclass=StaticPool)
    source_connection = source.connection().connection.dbapi_connection
    with engine.connect() as target:
        target_connection = target.connection.dbapi_connection
        if source_connection is None or target_connection is None:
            raise RuntimeError("SQLite backup connection is unavailable")
        source_connection.backup(target_connection)
    memory = sessionmaker(bind=engine)()
    try:
        yield memory
    finally:
        memory.close()
        engine.dispose()


def _version_for_config(data: dict[str, Any]) -> str:
    return "wf-" + hashlib.sha256(_canonical_config_content(data).encode()).hexdigest()[:12]


def _canonical_config_content(data: dict[str, Any]) -> str:
    content = dict(data)
    content.pop("version", None)
    return json.dumps(content, sort_keys=True, separators=(",", ":"))


def _validated_combination(
    validated_config: dict[str, Any], combination: dict[str, Any]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in combination:
        value: Any = validated_config
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                raise RuntimeError(f"validated strategy configuration is missing {path}")
            value = value[part]
        result[path] = value
    return result


def _number(value: Decimal | float | None) -> float | None:
    return None if value is None else float(value)


def _difference(left: Decimal | float | None, right: Decimal | float | None) -> float | None:
    return None if left is None or right is None else float(left) - float(right)
