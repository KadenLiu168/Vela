from datetime import date
from decimal import Decimal

import pytest
from vela_core.adjusted_price_projection import (
    ForwardAdjustedPrice,
    forward_adjusted_prices,
)
from vela_core.models import MarketPrice


def _price(trade_date: date, close: Decimal, factor: Decimal) -> MarketPrice:
    return MarketPrice(
        etf_id=1,
        trade_date=trade_date,
        open_price=close,
        high_price=close,
        low_price=close,
        close_price=close,
        factor_hfq=factor,
        volume=100,
    )


def test_forward_adjusted_prices_anchor_at_rebalance() -> None:
    # split on 2024-01-02: close halves, factor doubles
    prices = [
        _price(date(2024, 1, 1), Decimal("10.00"), Decimal("1.0")),
        _price(date(2024, 1, 2), Decimal("5.00"), Decimal("2.0")),
        _price(date(2024, 1, 3), Decimal("5.00"), Decimal("2.0")),
    ]
    anchor_factor = prices[2].factor_hfq

    result = forward_adjusted_prices(prices, rebalance_date=date(2024, 1, 3))

    assert result == [
        ForwardAdjustedPrice(
            trade_date=date(2024, 1, 1),
            price=prices[0].close_price * prices[0].factor_hfq / anchor_factor,
        ),
        ForwardAdjustedPrice(
            trade_date=date(2024, 1, 2),
            price=prices[1].close_price * prices[1].factor_hfq / anchor_factor,
        ),
        ForwardAdjustedPrice(
            trade_date=date(2024, 1, 3),
            price=prices[2].close_price * prices[2].factor_hfq / anchor_factor,
        ),
    ]


def test_forward_adjusted_price_at_rebalance_equals_unadjusted_close() -> None:
    prices = [
        _price(date(2024, 1, 1), Decimal("10.00"), Decimal("1.0")),
        _price(date(2024, 1, 2), Decimal("5.00"), Decimal("2.0")),
    ]

    result = forward_adjusted_prices(prices, rebalance_date=date(2024, 1, 2))

    # qfq(T) = close(T) * factor(T) / factor(T) == close(T) (unadjusted exec price)
    assert float(result[-1].price) == float(prices[1].close_price)
    assert result[-1].trade_date == date(2024, 1, 2)


def test_forward_adjusted_prices_raise_when_rebalance_not_in_series() -> None:
    prices = [_price(date(2024, 1, 1), Decimal("10.00"), Decimal("1.0"))]

    with pytest.raises(ValueError, match="rebalance date"):
        forward_adjusted_prices(prices, rebalance_date=date(2024, 1, 2))


def test_forward_adjusted_prices_empty_series_returns_empty() -> None:
    assert forward_adjusted_prices([], rebalance_date=date(2024, 1, 1)) == []


def test_forward_adjusted_ratio_equals_backward_adjusted_ratio() -> None:
    # ratio-based signals are identical across forward/backward viewpoints
    # because they differ only by the constant factor_hfq(T) which cancels.
    prices = [
        _price(date(2024, 1, 1), Decimal("10.00"), Decimal("1.0")),
        _price(date(2024, 1, 2), Decimal("12.00"), Decimal("1.0")),
        _price(date(2024, 1, 3), Decimal("6.00"), Decimal("2.0")),  # split after
    ]

    qfq = forward_adjusted_prices(prices, rebalance_date=date(2024, 1, 3))
    backward = [p.close_price * p.factor_hfq for p in prices]

    qfq_return = float(qfq[2].price / qfq[0].price - Decimal("1"))
    backward_return = float(backward[2] / backward[0] - Decimal("1"))

    assert qfq_return == pytest.approx(backward_return)


def test_forward_adjusted_prices_does_not_mutate_input() -> None:
    prices = [
        _price(date(2024, 1, 1), Decimal("10.00"), Decimal("1.0")),
        _price(date(2024, 1, 2), Decimal("5.00"), Decimal("2.0")),
    ]
    original_dates = [p.trade_date for p in prices]
    original_factors = [p.factor_hfq for p in prices]

    forward_adjusted_prices(prices, rebalance_date=date(2024, 1, 2))

    assert [p.trade_date for p in prices] == original_dates
    assert [p.factor_hfq for p in prices] == original_factors
