from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from vela_core import (
    DefensiveFallbackSelection,
    MomentumRanking,
    MomentumScore,
    TopNSelection,
    calculate_momentum_score,
    rank_momentum_scores,
    select_top_n_etfs,
    select_with_defensive_fallback,
)
from vela_core.models import Base, ETFInfo, MarketPrice
from vela_core.strategy_config import StrategyConfig


def test_calculates_weighted_momentum_score_from_complete_configured_windows() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("80"),
                20: Decimal("100"),
                30: Decimal("112"),
            },
            row_count=31,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )

    assert momentum_score == MomentumScore(
        etf_id=etf.id,
        as_of_date=_trade_date(30),
        short_return=Decimal("0.12"),
        long_return=Decimal("0.4"),
        score=Decimal("0.288"),
    )


def test_uses_configured_windows_instead_of_fixed_market_return_windows() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=7, long_window_days=13)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("65"),
                6: Decimal("100"),
                13: Decimal("130"),
            },
            row_count=14,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(13),
            config=config,
        )

    assert momentum_score.short_return == Decimal("0.3")
    assert momentum_score.long_return == Decimal("1")
    assert momentum_score.score == Decimal("0.72")


def test_reproduces_momentum_score_for_identical_inputs() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                0: Decimal("80"),
                20: Decimal("100"),
                30: Decimal("112"),
            },
            row_count=31,
        )

        first_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )
        second_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )

    assert first_score == second_score


def test_returns_none_score_when_a_configured_window_has_insufficient_history() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=5, long_window_days=20)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(
            session,
            etf_id=etf.id,
            prices_by_offset={
                5: Decimal("100"),
                10: Decimal("125"),
            },
            row_count=11,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(10),
            config=config,
        )

    assert momentum_score.short_return == Decimal("0.25")
    assert momentum_score.long_return is None
    assert momentum_score.score is None


def test_returns_none_score_when_current_price_is_missing() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        etf = _add_etf(session, symbol="SPY")
        _add_price_history(session, etf_id=etf.id, prices_by_offset={}, row_count=31)

        momentum_score = calculate_momentum_score(
            session,
            etf_id=etf.id,
            as_of_date=_trade_date(40),
            config=config,
        )

    assert momentum_score == MomentumScore(
        etf_id=etf.id,
        as_of_date=_trade_date(40),
        short_return=None,
        long_return=None,
        score=None,
    )


def test_uses_strategy_price_and_ignores_other_etf_histories() -> None:
    session_factory = _create_session_factory()
    config = _strategy_config(short_window_days=10, long_window_days=30)

    with session_factory() as session:
        target_etf = _add_etf(session, symbol="SPY")
        other_etf = _add_etf(session, symbol="QQQ")
        _add_price_history(
            session,
            etf_id=target_etf.id,
            prices_by_offset={
                0: Decimal("1"),
                20: Decimal("1"),
                30: Decimal("1"),
            },
            adjusted_close_by_offset={
                0: Decimal("80"),
                20: Decimal("100"),
                30: Decimal("112"),
            },
            row_count=31,
        )
        _add_price_history(
            session,
            etf_id=other_etf.id,
            prices_by_offset={
                0: Decimal("1000"),
                20: Decimal("1000"),
                30: Decimal("1000"),
            },
            row_count=31,
        )

        momentum_score = calculate_momentum_score(
            session,
            etf_id=target_etf.id,
            as_of_date=_trade_date(30),
            config=config,
        )

    assert momentum_score.short_return == Decimal("0.12")
    assert momentum_score.long_return == Decimal("0.4")
    assert momentum_score.score == Decimal("0.288")


def test_ranks_momentum_scores_by_score_descending() -> None:
    rankings = rank_momentum_scores(
        [
            _momentum_score(etf_id=1, score=Decimal("0.12")),
            _momentum_score(etf_id=2, score=Decimal("0.41")),
            _momentum_score(etf_id=3, score=Decimal("0.25")),
        ]
    )

    assert rankings == [
        MomentumRanking(
            etf_id=2,
            as_of_date=_trade_date(30),
            score=Decimal("0.41"),
            rank=1,
        ),
        MomentumRanking(
            etf_id=3,
            as_of_date=_trade_date(30),
            score=Decimal("0.25"),
            rank=2,
        ),
        MomentumRanking(
            etf_id=1,
            as_of_date=_trade_date(30),
            score=Decimal("0.12"),
            rank=3,
        ),
    ]


def test_ranks_equal_momentum_scores_by_etf_id_ascending() -> None:
    rankings = rank_momentum_scores(
        [
            _momentum_score(etf_id=3, score=Decimal("0.2")),
            _momentum_score(etf_id=1, score=Decimal("0.2")),
            _momentum_score(etf_id=2, score=Decimal("0.2")),
        ]
    )

    assert [ranking.etf_id for ranking in rankings] == [1, 2, 3]


def test_excludes_missing_momentum_scores_from_rankings() -> None:
    rankings = rank_momentum_scores(
        [
            _momentum_score(etf_id=1, score=Decimal("0.3")),
            _momentum_score(etf_id=2, score=None),
            _momentum_score(etf_id=3, score=Decimal("0.1")),
        ]
    )

    assert [ranking.etf_id for ranking in rankings] == [1, 3]


def test_assigns_continuous_ranks_after_excluding_missing_scores() -> None:
    rankings = rank_momentum_scores(
        [
            _momentum_score(etf_id=1, score=None),
            _momentum_score(etf_id=2, score=Decimal("0.2")),
            _momentum_score(etf_id=3, score=Decimal("0.4")),
        ]
    )

    assert [ranking.rank for ranking in rankings] == [1, 2]


def test_ranked_momentum_scores_support_top_n_selection() -> None:
    config = _strategy_config(short_window_days=10, long_window_days=30)
    rankings = rank_momentum_scores(
        [
            _momentum_score(etf_id=1, score=Decimal("0.3")),
            _momentum_score(etf_id=2, score=Decimal("0.1")),
            _momentum_score(etf_id=3, score=Decimal("0.5")),
        ]
    )

    top_rankings = rankings[: config.selection.top_n]

    assert [ranking.etf_id for ranking in top_rankings] == [3, 1]


def test_selects_configured_top_n_ranked_etfs() -> None:
    config = _strategy_config(short_window_days=10, long_window_days=30)
    rankings = [
        _momentum_ranking(etf_id=1, score=Decimal("0.4"), rank=2),
        _momentum_ranking(etf_id=2, score=Decimal("0.6"), rank=1),
        _momentum_ranking(etf_id=3, score=Decimal("0.2"), rank=3),
    ]

    selections = select_top_n_etfs(rankings, config)

    assert [selection.etf_id for selection in selections] == [2, 1]


def test_selected_etfs_include_rank_score_and_equal_target_weight() -> None:
    config = _strategy_config(short_window_days=10, long_window_days=30)
    rankings = [
        _momentum_ranking(etf_id=1, score=Decimal("0.4"), rank=1),
        _momentum_ranking(etf_id=2, score=Decimal("0.2"), rank=2),
    ]

    selections = select_top_n_etfs(rankings, config)

    assert selections == [
        TopNSelection(
            etf_id=1,
            rank=1,
            score=Decimal("0.4"),
            target_weight=Decimal("0.5"),
        ),
        TopNSelection(
            etf_id=2,
            rank=2,
            score=Decimal("0.2"),
            target_weight=Decimal("0.5"),
        ),
    ]


def test_selects_all_available_ranked_etfs_when_top_n_is_insufficient() -> None:
    config = _strategy_config(short_window_days=10, long_window_days=30)
    rankings = [
        _momentum_ranking(etf_id=1, score=Decimal("0.4"), rank=1),
    ]

    selections = select_top_n_etfs(rankings, config)

    assert selections == [
        TopNSelection(
            etf_id=1,
            rank=1,
            score=Decimal("0.4"),
            target_weight=Decimal("1"),
        ),
    ]


def test_selects_no_etfs_from_empty_rankings() -> None:
    config = _strategy_config(short_window_days=10, long_window_days=30)

    selections = select_top_n_etfs([], config)

    assert selections == []


def test_selects_defensive_asset_when_ranked_etfs_are_insufficient() -> None:
    config = _strategy_config(short_window_days=10, long_window_days=30)
    rankings = [
        _momentum_ranking(etf_id=1, score=Decimal("0.4"), rank=1),
    ]

    selections = select_with_defensive_fallback(rankings, config)

    assert selections == [
        DefensiveFallbackSelection(
            exchange="SSE",
            symbol="511010",
            rank=None,
            score=None,
            target_weight=Decimal("1"),
        )
    ]


def test_selects_top_n_without_defensive_asset_when_ranked_etfs_are_sufficient() -> None:
    config = _strategy_config(short_window_days=10, long_window_days=30)
    rankings = [
        _momentum_ranking(etf_id=1, score=Decimal("0.4"), rank=2),
        _momentum_ranking(etf_id=2, score=Decimal("0.6"), rank=1),
    ]

    selections = select_with_defensive_fallback(rankings, config)

    assert selections == [
        TopNSelection(
            etf_id=2,
            rank=1,
            score=Decimal("0.6"),
            target_weight=Decimal("0.5"),
        ),
        TopNSelection(
            etf_id=1,
            rank=2,
            score=Decimal("0.4"),
            target_weight=Decimal("0.5"),
        ),
    ]


def _create_session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def _add_etf(session: Session, symbol: str) -> ETFInfo:
    etf = ETFInfo(
        exchange="NYSEARCA",
        symbol=symbol,
        name=f"{symbol} ETF",
        currency="USD",
    )
    session.add(etf)
    session.flush()
    return etf


def _add_price_history(
    session: Session,
    *,
    etf_id: int,
    prices_by_offset: dict[int, Decimal],
    row_count: int,
    adjusted_close_by_offset: dict[int, Decimal] | None = None,
) -> None:
    adjusted_close_by_offset = adjusted_close_by_offset or {}
    session.add_all(
        _market_price(
            etf_id=etf_id,
            trade_date=_trade_date(offset),
            close_price=prices_by_offset.get(offset, Decimal("100")),
            adjusted_close=adjusted_close_by_offset.get(offset),
        )
        for offset in range(row_count)
    )
    session.commit()


def _trade_date(offset: int) -> date:
    return date(2026, 1, 1) + timedelta(days=offset)


def _momentum_score(*, etf_id: int, score: Decimal | None) -> MomentumScore:
    return MomentumScore(
        etf_id=etf_id,
        as_of_date=_trade_date(30),
        short_return=score,
        long_return=score,
        score=score,
    )


def _momentum_ranking(*, etf_id: int, score: Decimal, rank: int) -> MomentumRanking:
    return MomentumRanking(
        etf_id=etf_id,
        as_of_date=_trade_date(30),
        score=score,
        rank=rank,
    )


def _market_price(
    *,
    etf_id: int,
    trade_date: date,
    close_price: Decimal,
    adjusted_close: Decimal | None = None,
) -> MarketPrice:
    return MarketPrice(
        etf_id=etf_id,
        trade_date=trade_date,
        open_price=close_price,
        high_price=close_price,
        low_price=close_price,
        close_price=close_price,
        adjusted_close=adjusted_close,
        volume=1000,
    )


def _strategy_config(
    *,
    short_window_days: int,
    long_window_days: int,
    short_weight: float = 0.4,
    long_weight: float = 0.6,
) -> StrategyConfig:
    config: dict[str, Any] = {
        "strategy_id": "dual_momentum",
        "version": "v1",
        "universe_config": "config/etf_pool.yaml",
        "momentum": {
            "short_window_days": short_window_days,
            "long_window_days": long_window_days,
        },
        "score_weights": {
            "short": short_weight,
            "long": long_weight,
        },
        "trend_filter": {
            "moving_average_days": 120,
            "price_relation": "above",
        },
        "selection": {
            "top_n": 2,
        },
        "defense": {
            "asset": {
                "exchange": "SSE",
                "symbol": "511010",
            },
        },
        "costs": {
            "transaction_cost_bps": 5,
        },
    }
    return StrategyConfig.model_validate(config)
