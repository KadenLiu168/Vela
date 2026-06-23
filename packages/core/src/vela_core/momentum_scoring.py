from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.models import MarketPrice
from vela_core.strategy_config import StrategyConfig


@dataclass(frozen=True)
class MomentumScore:
    etf_id: int
    as_of_date: date
    short_return: Decimal | None
    long_return: Decimal | None
    score: Decimal | None


@dataclass(frozen=True)
class MomentumRanking:
    etf_id: int
    as_of_date: date
    score: Decimal
    rank: int


@dataclass(frozen=True)
class TopNSelection:
    etf_id: int
    rank: int
    score: Decimal
    target_weight: Decimal


@dataclass(frozen=True)
class DefensiveFallbackSelection:
    exchange: str
    symbol: str
    rank: int | None
    score: Decimal | None
    target_weight: Decimal


def calculate_momentum_score(
    session: Session,
    *,
    etf_id: int,
    as_of_date: date,
    config: StrategyConfig,
) -> MomentumScore:
    prices = list(
        session.scalars(
            select(MarketPrice)
            .where(MarketPrice.etf_id == etf_id)
            .where(MarketPrice.trade_date <= as_of_date)
            .order_by(MarketPrice.trade_date.desc())
            .limit(config.momentum.long_window_days + 1)
        )
    )

    if not prices or prices[0].trade_date != as_of_date:
        return MomentumScore(
            etf_id=etf_id,
            as_of_date=as_of_date,
            short_return=None,
            long_return=None,
            score=None,
        )

    short_return = _calculate_window_return(prices, config.momentum.short_window_days)
    long_return = _calculate_window_return(prices, config.momentum.long_window_days)
    score = _calculate_weighted_score(short_return, long_return, config)

    return MomentumScore(
        etf_id=etf_id,
        as_of_date=as_of_date,
        short_return=short_return,
        long_return=long_return,
        score=score,
    )


def rank_momentum_scores(scores: list[MomentumScore]) -> list[MomentumRanking]:
    eligible_scores = [(score, score.score) for score in scores if score.score is not None]
    sorted_scores = sorted(
        eligible_scores,
        key=lambda score_with_value: (-score_with_value[1], score_with_value[0].etf_id),
    )

    return [
        MomentumRanking(
            etf_id=score_with_value[0].etf_id,
            as_of_date=score_with_value[0].as_of_date,
            score=score_with_value[1],
            rank=rank,
        )
        for rank, score_with_value in enumerate(sorted_scores, start=1)
    ]


def select_top_n_etfs(
    rankings: list[MomentumRanking],
    config: StrategyConfig,
) -> list[TopNSelection]:
    selected_rankings = sorted(rankings, key=lambda ranking: ranking.rank)[: config.selection.top_n]
    if not selected_rankings:
        return []

    target_weight = Decimal("1") / Decimal(len(selected_rankings))
    return [
        TopNSelection(
            etf_id=ranking.etf_id,
            rank=ranking.rank,
            score=ranking.score,
            target_weight=target_weight,
        )
        for ranking in selected_rankings
    ]


def select_with_defensive_fallback(
    rankings: list[MomentumRanking],
    config: StrategyConfig,
) -> list[TopNSelection | DefensiveFallbackSelection]:
    if len(rankings) < config.selection.top_n:
        return [
            DefensiveFallbackSelection(
                exchange=config.defense.asset.exchange,
                symbol=config.defense.asset.symbol,
                rank=None,
                score=None,
                target_weight=Decimal("1"),
            )
        ]

    selections: list[TopNSelection | DefensiveFallbackSelection] = list(
        select_top_n_etfs(rankings, config)
    )
    return selections


def _calculate_window_return(
    prices: list[MarketPrice],
    window: int,
) -> Decimal | None:
    if len(prices) <= window:
        return None

    current_price = prices[0].strategy_price
    prior_price = prices[window].strategy_price
    return current_price / prior_price - Decimal("1")


def _calculate_weighted_score(
    short_return: Decimal | None,
    long_return: Decimal | None,
    config: StrategyConfig,
) -> Decimal | None:
    if short_return is None or long_return is None:
        return None

    short_weight = Decimal(str(config.score_weights.short))
    long_weight = Decimal(str(config.score_weights.long))
    return short_return * short_weight + long_return * long_weight
