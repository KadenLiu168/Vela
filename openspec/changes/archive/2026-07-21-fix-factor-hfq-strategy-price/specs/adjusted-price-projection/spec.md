## ADDED Requirements

### Requirement: MarketPrice strategy_price property removal

The system SHALL NOT expose a `strategy_price` property on the `MarketPrice` ORM model. Pricing normalization is the responsibility of the `adjusted_price_projection` module, not the persistence model.

#### Scenario: MarketPrice has no strategy_price attribute
- **WHEN** backend code accesses a `MarketPrice` instance
- **THEN** the instance does not have a `strategy_price` attribute or property
- **AND** accessing `market_price.strategy_price` raises `AttributeError`

#### Scenario: Forward_adjusted_prices is the canonical pricing entry point
- **WHEN** any consumer needs a strategy-usable price from `MarketPrice` data
- **THEN** the consumer MUST compute it through `forward_adjusted_prices()`, which normalizes `close_price × factor_hfq` against a rebalance-date anchor

## MODIFIED Requirements

### Requirement: Three price viewpoint contract

The system SHALL expose three distinct price viewpoints with fixed responsibilities across signal generation, backtest execution, and net value calculation. All signal and backtest ratio-calculation consumers SHALL derive prices through `forward_adjusted_prices()` anchored at the rebalance date of the computation, not through direct access to the backward-adjusted product `close_price × factor_hfq`.

#### Scenario: Signal generation is equivalent to forward-adjusted price

- **WHEN** backend code generates strategy signals or computes backtest signal decisions for a rebalance date
- **THEN** the signal calculation computes forward-adjusted prices via `forward_adjusted_prices(prices, rebalance_date=as_of_date)` and consumes the normalized `.price` field from the resulting `ForwardAdjustedPrice` values

#### Scenario: Backtest execution uses unadjusted close price
- **WHEN** backend code simulates trade execution for a rebalance date
- **THEN** the execution price is the unadjusted `close_price` for that date

#### Scenario: Net value calculation uses per-interval forward-adjusted prices
- **WHEN** backend code calculates portfolio net value or equity curve points
- **THEN** each close-to-close interval projects its previous and current rows through `forward_adjusted_prices` anchored at that interval's current date, so dividend reinvestment is captured and no artificial jump appears on ex-dividend dates
- **AND** the implementation does not cache one normalized Decimal per `(etf_id, trade_date)`, because the same row can have different valid anchors in adjacent intervals

### Requirement: Ratio-signal equivalence between forward and backward adjustment

The system SHALL produce identical ratio-based signal values whether computed from forward-adjusted or backward-adjusted price series, because the two differ only by the rebalance-date factor normalization constant.

#### Scenario: Momentum return is identical across adjustment viewpoints
- **WHEN** backend code computes a ratio-based signal (such as momentum return or trend comparison) over a window anchored at rebalance date `T`
- **THEN** the signal value computed from the forward-adjusted series equals the signal value computed from the backward-adjusted series
- **AND** this holds because forward-adjusted price equals backward-adjusted price divided by `factor_hfq(T)`, a constant that cancels in any ratio
