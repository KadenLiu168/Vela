# adjusted-price-projection Specification

## Purpose
TBD - created by archiving change add-adjusted-price-foundation. Update Purpose after archive.
## Requirements
### Requirement: Adjusted price projection from stored factors
The system SHALL derive forward-adjusted (qfq) price series from stored unadjusted close prices and backward-adjusted factors without persisting a separate adjusted price column.

#### Scenario: Forward-adjusted price is computed at query time
- **WHEN** backend code requests the forward-adjusted price series for an ETF over a window ending at rebalance date `T`
- **THEN** for each historical date `D` in the window, the forward-adjusted price equals `close_price(D) * factor_hfq(D) / factor_hfq(T)`

#### Scenario: Forward-adjusted price at rebalance date equals unadjusted close
- **WHEN** backend code requests the forward-adjusted price for the rebalance date `T` itself
- **THEN** the forward-adjusted price equals `close_price(T)` (the unadjusted execution price)

#### Scenario: Forward-adjusted prices are never persisted or cached
- **WHEN** backend code computes forward-adjusted prices
- **THEN** no forward-adjusted price value is written to a database column or materialized cache; the value is recomputed on each query

### Requirement: Three price viewpoint contract
The system SHALL expose three distinct price viewpoints with fixed responsibilities across signal generation, backtest execution, and net value calculation.

#### Scenario: Signal generation is equivalent to forward-adjusted price
- **WHEN** backend code generates strategy signals or computes backtest signal decisions for a rebalance date
- **THEN** the signal calculation produces values equivalent to consuming the forward-adjusted price series anchored at that rebalance date, and MAY consume the backward-adjusted `strategy_price` directly because ratio-signal equivalence holds

#### Scenario: Backtest execution uses unadjusted close price
- **WHEN** backend code simulates trade execution for a rebalance date
- **THEN** the execution price is the unadjusted `close_price` for that date

#### Scenario: Net value calculation uses backward-adjusted price
- **WHEN** backend code calculates portfolio net value or equity curve points
- **THEN** the calculation uses the backward-adjusted strategy price (`close_price * factor_hfq`) so that dividend reinvestment is implicitly captured and no artificial jump appears on ex-dividend dates

### Requirement: Ratio-signal equivalence between forward and backward adjustment
The system SHALL produce identical ratio-based signal values whether computed from forward-adjusted or backward-adjusted price series, because the two differ only by a normalization constant.

#### Scenario: Momentum return is identical across adjustment viewpoints
- **WHEN** backend code computes a ratio-based signal (such as momentum return or trend comparison) over a window
- **THEN** the signal value computed from the forward-adjusted series equals the signal value computed from the backward-adjusted series
- **AND** this holds because forward-adjusted price equals backward-adjusted price divided by the rebalance-date backward-adjusted price, a constant that cancels in any ratio

