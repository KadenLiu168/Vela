## ADDED Requirements

### Requirement: Market price upsert factor update

The system SHALL include `factor_hfq` in the SQLite upsert `ON CONFLICT DO UPDATE SET` clause so that when a corporate action triggers a full refetch, existing rows' backward-adjustment factors are updated alongside open/high/low/close/volume, maintaining consistent factor anchoring across all rows for a given ETF.

#### Scenario: Factor is updated on upsert conflict
- **WHEN** backend code upserts a market price whose `etf_id` and `trade_date` already exist in SQLite and the incoming `factor_hfq` differs from the stored value
- **THEN** the system updates the stored `factor_hfq` to the incoming value
- **AND** the update is part of the same `ON CONFLICT DO UPDATE` statement that updates open/high/low/close/volume

#### Scenario: Factor update is a no-op when unchanged
- **WHEN** backend code upserts a market price whose `factor_hfq` equals the stored value
- **THEN** the stored `factor_hfq` remains unchanged
- **AND** the upsert count still reports the row as updated (not inserted)

#### Scenario: Full refetch repairs an existing factor series
- **WHEN** a successful full market-data fetch receives rows for an active ETF already stored with an earlier factor anchoring base
- **THEN** the conflict updates rewrite every fetched existing row's `factor_hfq` to the upstream value
- **AND** a local database created before this change is repaired for its active ETF universe by running the existing full fetch command without `--incremental` and obtaining `success` with no failed symbols

#### Scenario: Partial full fetch is not a complete repair
- **WHEN** a full market-data fetch succeeds for at least one active ETF but fails for another and returns `partial`
- **THEN** the caller-managed session commits updates for the successfully fetched ETFs according to the existing partial-fetch contract
- **AND** the database is not considered fully repaired until the provider failure is resolved and a later full fetch returns `success` with no failed symbols
- **AND** inactive ETF history is not changed by the full fetch

#### Scenario: New rows always receive their factor
- **WHEN** backend code inserts a market price whose `etf_id` and `trade_date` do not exist in SQLite
- **THEN** the new row receives the `factor_hfq` from the INSERT values

## MODIFIED Requirements

### Requirement: Strategy price selection

The system SHALL define the strategy calculation price as the forward-adjusted (qfq) price, computed by normalizing the backward-adjusted price (`close_price × factor_hfq`) against the rebalance-date anchor via the `forward_adjusted_prices` function in `adjusted_price_projection`. The `MarketPrice` ORM model SHALL NOT expose a `strategy_price` property.

#### Scenario: Forward-adjusted price is the canonical strategy price
- **WHEN** a consumer needs the strategy price for a date within a window anchored at rebalance date `T`
- **THEN** the consumer computes `forward_adjusted_prices(prices, rebalance_date=T)` and uses the resulting `.price` field
- **AND** the consumer does not access `MarketPrice.strategy_price` (the property does not exist on the ORM model)

#### Scenario: Forward-adjusted price at rebalance date equals unadjusted close
- **WHEN** backend code computes the forward-adjusted price for the rebalance date `T` itself
- **THEN** the forward-adjusted price equals `close_price(T)`, matching the actual execution price on that date

### Requirement: Backward-adjustment factor consistency check on incremental fetch

The system SHALL detect corporate actions on every incremental market price fetch by comparing the stored last-row `factor_hfq` against the upstream same-date factor value. When a factor mismatch is detected, the system SHALL trigger a full refetch that updates existing rows' `factor_hfq` (via the upsert conflict SET) to maintain cross-batch factor anchor consistency.

#### Scenario: Factor match appends new rows
- **WHEN** an incremental fetch compares the stored last-row `factor_hfq` against the upstream same-date factor value and the relative difference is below the configured tolerance
- **THEN** the system appends the newly fetched rows without modifying existing rows

#### Scenario: Factor mismatch triggers full refetch for the ETF
- **WHEN** an incremental fetch compares the stored last-row `factor_hfq` against the upstream same-date factor value and the relative difference meets or exceeds the configured tolerance
- **THEN** the system refetches the full history for that ETF from the earliest available date and rewrites the factor series by updating existing rows' `factor_hfq` to match the recalculated upstream values

#### Scenario: Factor mismatch records a quality warning
- **WHEN** the consistency check detects a factor mismatch (corporate action) for an ETF
- **THEN** the system records a quality warning in the existing fetch log `quality_warnings` field, consistent with the trading-day-gap and duplicate-trade-date detection mechanisms

### Requirement: Market price window return calculation

The system SHALL calculate 20 / 60 / 120 trading-day returns for a single ETF from stored `MarketPrice` history using forward-adjusted prices.

#### Scenario: Calculate complete window returns
- **WHEN** backend code calculates market price returns for an ETF and `as_of_date` with enough prior trading-day `MarketPrice` rows
- **THEN** the system returns 20-day, 60-day, and 120-day returns for that ETF
- **AND** each return uses forward-adjusted prices computed via `forward_adjusted_prices` anchored at `as_of_date`

#### Scenario: Use canonical projection for return calculation
- **WHEN** the return calculation has an ascending price window containing `as_of_date`
- **THEN** it calls `forward_adjusted_prices(prices, rebalance_date=as_of_date)` after the missing-current-price guard
- **AND** it calculates each return from the resulting `.price` values

#### Scenario: Count windows by trading price rows
- **WHEN** backend code calculates a 20-day return
- **THEN** the prior price is the 20th earlier `MarketPrice` row for the same ETF ordered by `trade_date`
- **AND** the same trading-row counting rule applies to 60-day and 120-day returns

#### Scenario: Missing historical data returns null windows
- **WHEN** backend code calculates market price returns for an ETF whose history is insufficient for one or more windows
- **THEN** each insufficient window return is null
- **AND** windows with enough history still return calculated values

#### Scenario: Missing current price returns null windows
- **WHEN** backend code calculates market price returns for an ETF and no `MarketPrice` exists for the requested `as_of_date`
- **THEN** the 20-day, 60-day, and 120-day returns are null

#### Scenario: Isolate ETF histories
- **WHEN** market prices exist for multiple ETFs
- **THEN** the return calculation only uses `MarketPrice` rows for the requested ETF

### Requirement: Market price 120-day moving average calculation

The system SHALL calculate a 120-trading-day moving average for a single ETF from stored `MarketPrice` history using forward-adjusted prices.

#### Scenario: Calculate complete 120-day moving average
- **WHEN** backend code calculates the 120-day moving average for an ETF and `as_of_date` with 120 same-ETF `MarketPrice` rows through that date
- **THEN** the system returns the arithmetic average of those 120 forward-adjusted prices for that ETF, anchored at `as_of_date`

#### Scenario: Use canonical projection for moving average calculation
- **WHEN** the moving-average calculation has the required ascending price window containing `as_of_date`
- **THEN** it calls `forward_adjusted_prices(prices, rebalance_date=as_of_date)` after the missing-current-price guard
- **AND** it calculates the arithmetic average from the resulting `.price` values

#### Scenario: Count moving average window by trading price rows
- **WHEN** backend code calculates the 120-day moving average for an ETF and `as_of_date`
- **THEN** the moving average window includes the `as_of_date` row and the 119 earlier `MarketPrice` rows for the same ETF ordered by `trade_date`

#### Scenario: Missing historical data returns null moving average
- **WHEN** backend code calculates the 120-day moving average for an ETF with fewer than 120 same-ETF `MarketPrice` rows through `as_of_date`
- **THEN** the moving average value is null

#### Scenario: Missing current price returns null moving average
- **WHEN** backend code calculates the 120-day moving average for an ETF and no `MarketPrice` exists for the requested `as_of_date`
- **THEN** the moving average value is null

#### Scenario: Isolate ETF histories
- **WHEN** market prices exist for multiple ETFs
- **THEN** the moving average calculation only uses `MarketPrice` rows for the requested ETF

## REMOVED Requirements

### Requirement: Corporate-action factor is append-only

**Reason**: The backward-adjustment factor is mathematically recomputed relative to the latest date whenever a corporate action occurs. The append-only semantics contradict the factor's mathematical definition and produce cross-batch anchor inconsistency at corporate-action boundary dates, silently corrupting all ratio-based signals.

**Migration**: Replace with "Market price upsert factor update" (ADDED above). The upsert now updates `factor_hfq` on conflict alongside all other price fields, eliminating anchor inconsistency. Corporate action detection via factor comparison at the boundary date continues to work — the difference is that the subsequent full refetch now correctly updates existing rows' factors.
