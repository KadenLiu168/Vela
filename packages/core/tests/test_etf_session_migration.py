from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command

REPO_ROOT = Path(__file__).resolve().parents[3]
PREVIOUS_REVISION = "20260810_0019"


def _alembic_config(database_path: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{database_path}")
    return config


def test_temporal_reference_migration_preserves_history_and_downgrades(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "temporal-reference.db"
    config = _alembic_config(database_path)
    command.upgrade(config, PREVIOUS_REVISION)
    engine = create_engine(f"sqlite+pysqlite:///{database_path}")

    with engine.begin() as connection:
        etf_id = connection.execute(
            text(
                "INSERT INTO etf_info "
                "(exchange, symbol, name, currency, inception_date, is_active) "
                "VALUES ('SSE', '510300', 'CSI 300 ETF', 'CNY', '2012-05-01', 1) "
                "RETURNING id"
            )
        ).scalar_one()
        connection.execute(
            text(
                "INSERT INTO market_price "
                "(etf_id, trade_date, open_price, high_price, low_price, close_price, "
                "factor_hfq) VALUES (:etf_id, '2024-01-02', 1, 1, 1, 1, 1)"
            ),
            {"etf_id": etf_id},
        )

    command.upgrade(config, "head")
    with engine.connect() as connection:
        inspector = inspect(connection)
        etf_columns = {column["name"]: column for column in inspector.get_columns("etf_info")}
        status_columns = {
            column["name"]: column for column in inspector.get_columns("etf_session_status")
        }
        assert etf_columns["listing_date"]["nullable"] is True
        assert {
            "id",
            "etf_id",
            "trade_date",
            "status",
            "reason",
            "source_uri",
            "source_published_date",
            "share_ratio",
            "created_at",
            "updated_at",
        } <= set(status_columns)
        assert "etf_session_status" in inspector.get_table_names()
        assert {
            "ix_etf_session_status_etf_trade_date",
            "ix_etf_session_status_trade_date",
        } <= {index["name"] for index in inspector.get_indexes("etf_session_status")}
        assert connection.execute(text("SELECT COUNT(*) FROM etf_info")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM market_price")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM etf_session_status")).scalar_one() == 0

        valid = {
            "etf_id": etf_id,
            "trade_date": date(2024, 1, 3),
            "status": "full_day_suspension",
            "reason": "holder_meeting",
            "source_uri": "https://example.test/announcement",
            "source_published_date": date(2024, 1, 2),
            "share_ratio": None,
        }
        connection.execute(
            text(
                "INSERT INTO etf_session_status "
                "(etf_id, trade_date, status, reason, source_uri, "
                "source_published_date, share_ratio) "
                "VALUES (:etf_id, :trade_date, :status, :reason, :source_uri, "
                ":source_published_date, :share_ratio)"
            ),
            valid,
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO etf_session_status "
                    "(etf_id, trade_date, status, reason, source_uri, source_published_date) "
                    "VALUES (:etf_id, :trade_date, 'unsupported', 'reason', 'uri', '2024-01-02')"
                ),
                {"etf_id": etf_id, "trade_date": date(2024, 1, 4)},
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO etf_session_status "
                    "(etf_id, trade_date, status, reason, source_uri, "
                    "source_published_date, share_ratio) "
                    "VALUES (:etf_id, :trade_date, 'corporate_action_halt', 'split', 'uri', "
                    "'2024-01-02', :share_ratio)"
                ),
                {"etf_id": etf_id, "trade_date": date(2024, 1, 5), "share_ratio": 0},
            )

    command.downgrade(config, PREVIOUS_REVISION)
    with engine.connect() as connection:
        inspector = inspect(connection)
        assert "listing_date" not in {
            column["name"] for column in inspector.get_columns("etf_info")
        }
        assert "etf_session_status" not in inspector.get_table_names()
        assert connection.execute(text("SELECT COUNT(*) FROM etf_info")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM market_price")).scalar_one() == 1
