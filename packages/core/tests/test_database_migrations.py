import importlib.util
from pathlib import Path
from typing import Any

import alembic.command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from vela_core.models import Base

ROOT = Path(__file__).parents[3]
CURRENT_TABLES = set(Base.metadata.tables)
OBSOLETE_TABLES = {"backtest_equity_point"}


def test_alembic_target_metadata_includes_all_persisted_model_tables() -> None:
    alembic_env = _load_alembic_env()

    assert set(alembic_env.target_metadata.tables) == CURRENT_TABLES


def test_sqlite_upgrade_head_creates_current_schema(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        assert _database_revision(engine) == _current_head(config)
        assert CURRENT_TABLES <= tables
        assert OBSOLETE_TABLES.isdisjoint(tables)
    finally:
        engine.dispose()


def test_sqlite_migration_head_matches_orm_metadata(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
    finally:
        engine.dispose()


def test_strategy_signal_provenance_migration_backfills_and_round_trips(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    previous_revision = "20260709_0010"
    alembic.command.upgrade(config, previous_revision)

    engine = _create_engine(config)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO strategy_signal "
                    "(signal_date, strategy_id, config_version, generated_at, status, result) "
                    "VALUES ('2026-06-22', 'Dual_momentum', 'v1', "
                    "'2026-06-22 09:30:00', 'success', 'hold')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_id, config_version, start_date, end_date, parameters_json, "
                    "started_at, finished_at, status) "
                    "VALUES ('Dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', '2026-02-01 09:05:00', 'success')"
                )
            )
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        columns = {column["name"]: column for column in inspector.get_columns("strategy_signal")}
        checks = {
            constraint["name"] for constraint in inspector.get_check_constraints("strategy_signal")
        }
        foreign_keys = inspector.get_foreign_keys("strategy_signal")
        indexes = {index["name"] for index in inspector.get_indexes("strategy_signal")}

        assert columns["source"]["nullable"] is False
        assert columns["source"]["type"].length == 16
        assert columns["backtest_run_id"]["nullable"] is True
        assert checks >= {"ck_strategy_signal_source", "ck_strategy_signal_backtest_link"}
        assert any(
            foreign_key["constrained_columns"] == ["backtest_run_id"]
            and foreign_key["referred_table"] == "backtest_run"
            for foreign_key in foreign_keys
        )
        assert "ix_strategy_signal_backtest_run_id" in indexes

        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT source, backtest_run_id FROM strategy_signal")
            ).one() == ("legacy", None)
            assert connection.execute(text("SELECT COUNT(*) FROM backtest_run")).scalar_one() == 1
    finally:
        engine.dispose()

    alembic.command.downgrade(config, previous_revision)
    engine = _create_engine(config)
    try:
        downgraded_columns = {
            column["name"] for column in inspect(engine).get_columns("strategy_signal")
        }
        assert "source" not in downgraded_columns
        assert "backtest_run_id" not in downgraded_columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
            assert connection.execute(
                text("SELECT source, backtest_run_id FROM strategy_signal")
            ).one() == ("legacy", None)
    finally:
        engine.dispose()


def test_data_snapshot_migration_round_trips_and_matches_metadata(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    previous_revision = "20260719_0011"
    alembic.command.upgrade(config, previous_revision)

    engine = _create_engine(config)
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("backtest_run")}
        assert "data_snapshot_json" not in columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        column = next(
            candidate
            for candidate in inspect(engine).get_columns("backtest_run")
            if candidate["name"] == "data_snapshot_json"
        )
        assert column["nullable"] is True
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_id, config_version, start_date, end_date, parameters_json, "
                    "started_at, status, data_snapshot_json) "
                    "VALUES ('dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', 'success', :snapshot)"
                ),
                {"snapshot": '{"data_checksum":"abc"}'},
            )
            assert (
                connection.execute(text("SELECT data_snapshot_json FROM backtest_run")).scalar_one()
                == '{"data_checksum":"abc"}'
            )
    finally:
        engine.dispose()

    alembic.command.downgrade(config, previous_revision)
    engine = _create_engine(config)
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("backtest_run")}
        assert "data_snapshot_json" not in columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
    finally:
        engine.dispose()


def test_benchmark_migration_preserves_legacy_runs_and_downgrades_cleanly(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    previous_revision = "20260725_0012"
    alembic.command.upgrade(config, previous_revision)

    engine = _create_engine(config)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_id, config_version, start_date, end_date, parameters_json, "
                    "started_at, status) "
                    "VALUES ('dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', 'success')"
                )
            )
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        assert {"backtest_benchmark", "backtest_benchmark_equity_curve"} <= set(
            inspector.get_table_names()
        )
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM backtest_run")).scalar_one() == 1
            assert (
                connection.execute(text("SELECT COUNT(*) FROM backtest_benchmark")).scalar_one()
                == 0
            )
    finally:
        engine.dispose()

    alembic.command.downgrade(config, previous_revision)
    engine = _create_engine(config)
    try:
        assert "backtest_benchmark" not in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_expanded_metric_migration_preserves_legacy_values_and_downgrades_cleanly(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    previous_revision = "20260803_0013"
    alembic.command.upgrade(config, previous_revision)

    engine = _create_engine(config)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_id, config_version, start_date, end_date, parameters_json, "
                    "started_at, status, total_return, annualized_return, max_drawdown, "
                    "sharpe_ratio, volatility) "
                    "VALUES ('dual_momentum', 'v1', '2026-01-01', '2026-01-03', '{}', "
                    "'2026-02-01 09:00:00', 'success', 0.12, 0.18, -0.05, 1.1, 0.14)"
                )
            )
            run_id = connection.execute(text("SELECT id FROM backtest_run")).scalar_one()
            connection.execute(
                text(
                    "INSERT INTO backtest_benchmark "
                    "(backtest_run_id, benchmark_key, display_name, total_return, "
                    "annualized_return, max_drawdown, sharpe_ratio, volatility) "
                    "VALUES (:run_id, 'equal_weight_monthly', 'Equal weight', "
                    "0.1, 0.12, -0.04, 0.9, 0.1)"
                ),
                {"run_id": run_id},
            )
            benchmark_id = connection.execute(
                text("SELECT id FROM backtest_benchmark")
            ).scalar_one()
            connection.execute(
                text(
                    "INSERT INTO backtest_equity_curve "
                    "(backtest_run_id, trade_date, net_value, cash, market_value, "
                    "total_assets, positions_json) "
                    "VALUES (:run_id, '2026-01-02', 1.01, 0.01, 1.0, 1.01, '[]')"
                ),
                {"run_id": run_id},
            )
            connection.execute(
                text(
                    "INSERT INTO backtest_benchmark_equity_curve "
                    "(benchmark_id, trade_date, net_value) "
                    "VALUES (:benchmark_id, '2026-01-02', 1.02)"
                ),
                {"benchmark_id": benchmark_id},
            )
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        expected_strategy = {
            "sortino_ratio",
            "calmar_ratio",
            "longest_drawdown_duration_sessions",
            "longest_drawdown_peak_date",
            "longest_drawdown_trough_date",
            "longest_drawdown_recovery_date",
        }
        expected_benchmark = expected_strategy | {"tracking_error", "information_ratio"}
        assert expected_strategy <= {
            column["name"] for column in inspector.get_columns("backtest_run")
        }
        assert expected_benchmark <= {
            column["name"] for column in inspector.get_columns("backtest_benchmark")
        }
        with engine.connect() as connection:
            assert connection.execute(
                text(
                    "SELECT total_return, annualized_return, max_drawdown, sharpe_ratio, "
                    "volatility, sortino_ratio, calmar_ratio, "
                    "longest_drawdown_duration_sessions "
                    "FROM backtest_run"
                )
            ).one() == (0.12, 0.18, -0.05, 1.1, 0.14, None, None, None)
            assert connection.execute(
                text(
                    "SELECT tracking_error, information_ratio, "
                    "longest_drawdown_duration_sessions FROM backtest_benchmark"
                )
            ).one() == (None, None, None)
            assert connection.execute(
                text(
                    "SELECT trade_date, net_value, cash, market_value, total_assets, "
                    "positions_json FROM backtest_equity_curve"
                )
            ).one() == ("2026-01-02", 1.01, 0.01, 1, 1.01, "[]")
            assert connection.execute(
                text("SELECT trade_date, net_value FROM backtest_benchmark_equity_curve")
            ).one() == ("2026-01-02", 1.02)
    finally:
        engine.dispose()

    alembic.command.downgrade(config, previous_revision)
    engine = _create_engine(config)
    try:
        assert "sortino_ratio" not in {
            column["name"] for column in inspect(engine).get_columns("backtest_run")
        }
        assert "tracking_error" not in {
            column["name"] for column in inspect(engine).get_columns("backtest_benchmark")
        }
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT total_return, annualized_return, max_drawdown FROM backtest_run")
            ).one() == (0.12, 0.18, -0.05)
            assert connection.execute(
                text(
                    "SELECT trade_date, net_value, cash, market_value, total_assets, "
                    "positions_json FROM backtest_equity_curve"
                )
            ).one() == ("2026-01-02", 1.01, 0.01, 1, 1.01, "[]")
            assert connection.execute(
                text("SELECT trade_date, net_value FROM backtest_benchmark_equity_curve")
            ).one() == ("2026-01-02", 1.02)
    finally:
        engine.dispose()


def test_benchmark_regime_metric_migration_preserves_legacy_values_and_downgrades_cleanly(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    previous_revision = "20260804_0015"
    alembic.command.upgrade(config, previous_revision)

    engine = _create_engine(config)
    try:
        with engine.begin() as connection:
            run_id = connection.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_id, config_version, start_date, end_date, parameters_json, "
                    "started_at, finished_at, status, total_return, annualized_return, "
                    "max_drawdown, sharpe_ratio, volatility) "
                    "VALUES ('dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', '2026-02-01 09:05:00', 'success', "
                    "0.12, 0.18, -0.05, 1.10, 0.20) RETURNING id"
                )
            ).scalar_one()
            connection.execute(
                text(
                    "INSERT INTO backtest_benchmark "
                    "(backtest_run_id, benchmark_key, display_name, total_return, "
                    "annualized_return, max_drawdown, sharpe_ratio, volatility, "
                    "tracking_error, information_ratio) "
                    "VALUES (:run_id, 'csi_300_buy_hold', 'CSI 300 buy-and-hold', "
                    "0.1, 0.12, -0.04, 0.9, 0.1, 0.03, 0.5)"
                ),
                {"run_id": run_id},
            )
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        expected = {
            "capm_alpha",
            "capm_beta",
            "capm_r_squared",
            "capm_observation_count",
            "up_capture_ratio",
            "up_capture_observation_count",
            "down_capture_ratio",
            "down_capture_observation_count",
        }
        columns = {column["name"] for column in inspector.get_columns("backtest_benchmark")}
        assert expected <= columns
        with engine.connect() as connection:
            assert connection.execute(
                text(
                    "SELECT total_return, annualized_return, max_drawdown, sharpe_ratio, "
                    "volatility, tracking_error, information_ratio "
                    "FROM backtest_benchmark"
                )
            ).one() == (0.1, 0.12, -0.04, 0.9, 0.1, 0.03, 0.5)
            assert connection.execute(
                text(
                    "SELECT capm_alpha, capm_beta, capm_r_squared, capm_observation_count, "
                    "up_capture_ratio, up_capture_observation_count, "
                    "down_capture_ratio, down_capture_observation_count "
                    "FROM backtest_benchmark"
                )
            ).one() == (None, None, None, None, None, None, None, None)
    finally:
        engine.dispose()

    alembic.command.downgrade(config, previous_revision)
    engine = _create_engine(config)
    try:
        columns = {column["name"] for column in inspect(engine).get_columns("backtest_benchmark")}
        assert expected.isdisjoint(columns)
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT benchmark_key, tracking_error FROM backtest_benchmark")
            ).one() == ("csi_300_buy_hold", 0.03)
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")
    engine = _create_engine(config)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
    finally:
        engine.dispose()


def test_migration_adds_strategy_id_and_renames_backtest_strategy_column(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "20260618_0006")

    engine = _create_engine(config)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO strategy_signal "
                    "(signal_date, config_version, generated_at, status, result) "
                    "VALUES ('2026-06-22', 'v1', '2026-06-22 09:30:00', 'success', 'hold')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO backtest_run "
                    "(strategy_name, config_version, start_date, end_date, parameters_json, "
                    "started_at, finished_at, status, total_return, annualized_return, "
                    "max_drawdown, sharpe_ratio, volatility) "
                    "VALUES ('dual_momentum', 'v1', '2026-01-01', '2026-01-31', '{}', "
                    "'2026-02-01 09:00:00', '2026-02-01 09:05:00', 'success', "
                    "0.12, 0.18, -0.05, 1.10, 0.20)"
                )
            )
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        signal_columns = {col["name"] for col in inspector.get_columns("strategy_signal")}
        assert "strategy_id" in signal_columns

        backtest_columns = {col["name"] for col in inspector.get_columns("backtest_run")}
        assert "strategy_id" in backtest_columns
        assert "strategy_name" not in backtest_columns

        backtest_indexes = {idx["name"] for idx in inspector.get_indexes("backtest_run")}
        assert "ix_backtest_run_strategy_config" in backtest_indexes

        signal_indexes = {idx["name"] for idx in inspector.get_indexes("strategy_signal")}
        assert "ix_strategy_signal_strategy_config" in signal_indexes

        with engine.connect() as conn:
            signal_strategy_ids = conn.execute(
                text("SELECT strategy_id FROM strategy_signal ORDER BY id")
            ).fetchall()
            assert signal_strategy_ids == [("Dual_momentum",)]

            backtest_strategy_ids = conn.execute(
                text("SELECT strategy_id FROM backtest_run ORDER BY id")
            ).fetchall()
            assert backtest_strategy_ids == [("Dual_momentum",)]
    finally:
        engine.dispose()


def test_migration_adds_quality_warnings_column_to_data_fetch_log(
    tmp_path: Path,
) -> None:
    config = _alembic_config(tmp_path / "vela.db")
    alembic.command.upgrade(config, "20260708_0007")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("data_fetch_log")}
        assert "quality_warnings" not in columns
    finally:
        engine.dispose()

    alembic.command.upgrade(config, "head")

    engine = _create_engine(config)
    try:
        inspector = inspect(engine)
        column = next(
            col
            for col in inspector.get_columns("data_fetch_log")
            if col["name"] == "quality_warnings"
        )
        assert column["nullable"] is True
    finally:
        engine.dispose()


def _load_alembic_env() -> Any:
    env_path = ROOT / "alembic" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", env_path)

    assert spec is not None
    assert spec.loader is not None

    alembic_env = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alembic_env)
    return alembic_env


def _alembic_config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{database_path}")
    return config


def _create_engine(config: Config) -> Engine:
    database_url = config.get_main_option("sqlalchemy.url")
    assert database_url is not None
    return create_engine(database_url)


def _current_head(config: Config) -> str:
    head = ScriptDirectory.from_config(config).get_current_head()
    assert head is not None
    return head


def _database_revision(engine: Engine) -> str:
    with engine.connect() as connection:
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one()

    return str(revision)
