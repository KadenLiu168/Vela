"""JoinQuant integration smoke test.

Requires real JoinQuant credentials in the environment (``JQ_USERNAME`` /
``JQ_PASSWORD``). Skipped automatically when credentials are absent, so this
test never blocks credential-less contributors or CI without secrets.

Its purpose is to verify jqdatasdk's real output contract (date format, index
name, auth flow, column shape) that the fake-module unit tests cannot cover.
The persistence path is already exercised by the existing integration tests
with ``ControlledMarketDataProvider`` and is intentionally not duplicated here.
"""

import os
from datetime import date, timedelta

import pytest
from dotenv import load_dotenv

# Load .env before evaluating the skipif, so credentials placed in a gitignored
# .env (rather than exported into the shell) are visible at collection time.
load_dotenv()

pytestmark = pytest.mark.skipif(
    not os.environ.get("JQ_USERNAME") or not os.environ.get("JQ_PASSWORD"),
    reason="JoinQuant credentials (JQ_USERNAME/JQ_PASSWORD) not set",
)


def test_joinquant_fetches_real_etf_daily_prices() -> None:
    from vela_core import JoinQuantMarketDataProvider

    provider = JoinQuantMarketDataProvider()
    end = date.today()
    start = end - timedelta(days=90)

    prices = provider.get_etf_daily_prices("510300", start_date=start, end_date=end)

    assert len(prices) >= 1
    for price in prices:
        assert price.symbol == "510300"
        assert price.trade_date <= end
        assert price.open_price > 0
        assert price.high_price >= price.open_price
        assert price.high_price >= price.low_price
        assert price.high_price >= price.close_price
        assert price.low_price <= price.open_price
        assert price.low_price <= price.close_price
        assert price.close_price > 0
        assert price.factor > 0
        if price.volume is not None:
            assert price.volume >= 0

    dates = [p.trade_date for p in prices]
    assert dates == sorted(dates)
