## MODIFIED Requirements

### Requirement: Market price ORM model
The system SHALL define a `MarketPrice` SQLAlchemy ORM model for ETF daily market prices.

#### Scenario: Model exposes ETF daily price fields
- **WHEN** backend code inspects the `MarketPrice` model table
- **THEN** the table includes columns for `id`, `etf_id`, `trade_date`, `open_price`, `high_price`, `low_price`, `close_price`, `factor_hfq`, `volume`, `created_at`, and `updated_at`
- **AND** the table does NOT include an `adjusted_close` column

#### Scenario: Market price references ETF metadata
- **WHEN** backend code inspects the `MarketPrice` model table
- **THEN** `etf_id` references the `ETFInfo` table primary key

#### Scenario: Backward-adjustment factor is required and high precision
- **WHEN** backend code inspects the `MarketPrice` model table
- **THEN** `factor_hfq` is a non-nullable high-precision numeric column (scale 12) holding the backward-adjustment factor for that trade date

### Requirement: Strategy price selection
The system SHALL define the strategy calculation price as the backward-adjusted price, computed as unadjusted close multiplied by the backward-adjustment factor.

#### Scenario: Strategy price is backward-adjusted
- **WHEN** a market price row has a non-null `factor_hfq`
- **THEN** strategy calculations use `close_price * factor_hfq` as the backward-adjusted price value

#### Scenario: Forward-adjusted price is derived at query time
- **WHEN** backend code needs the forward-adjusted price for a date within a window anchored at rebalance date `T`
- **THEN** the forward-adjusted price equals `close_price * factor_hfq` divided by the rebalance-date `factor_hfq`, and is not stored as a column

### Requirement: Provider daily price to market price mapping
The system SHALL provide a tested mapping from normalized provider daily price values into internal `MarketPrice` fields.

#### Scenario: Map provider daily price fields
- **WHEN** backend code maps a provider daily price value with an internal ETF id
- **THEN** the resulting `MarketPrice` row uses that ETF id and preserves trade date, open price, high price, low price, close price, backward-adjustment factor, and volume values

#### Scenario: Preserve explicit field types
- **WHEN** backend code maps a provider daily price value into a `MarketPrice` row
- **THEN** trade date remains a date value, price fields remain decimal values, factor remains a high-precision decimal value, and volume remains an optional integer value

#### Scenario: Keep provider mapping independent from ETF lookup
- **WHEN** backend code maps a provider daily price value into a `MarketPrice` row
- **THEN** the mapper does not query ETF metadata or infer `etf_id` from the provider symbol

## ADDED Requirements

### Requirement: Backward-adjustment factor consistency check on incremental fetch
The system SHALL detect corporate actions on every incremental market price fetch by comparing the stored last-row `factor_hfq` against the upstream same-date factor value. Because the stored factor is an append-only snapshot immune to upstream retroactive factor revisions, this check's sole purpose is to detect corporate actions so that newly fetched rows receive the correct factor (incremental fetch only pulls unadjusted prices and cannot otherwise observe factor changes).

#### Scenario: Factor match appends new rows
- **WHEN** an incremental fetch compares the stored last-row `factor_hfq` against the upstream same-date factor value and the relative difference is below the configured tolerance
- **THEN** the system appends the newly fetched rows using the stored factor without modifying existing rows

#### Scenario: Factor mismatch triggers full refetch for the ETF
- **WHEN** an incremental fetch compares the stored last-row `factor_hfq` against the upstream same-date factor value and the relative difference meets or exceeds the configured tolerance
- **THEN** the system refetches the full history for that ETF from the earliest available date and rewrites the factor series as an append-only operation without leaving mixed-factor rows

#### Scenario: Factor mismatch records a quality warning
- **WHEN** the consistency check detects a factor mismatch (corporate action) for an ETF
- **THEN** the system records a quality warning in the existing fetch log `quality_warnings` field, consistent with the trading-day-gap and duplicate-trade-date detection mechanisms

### Requirement: Corporate-action factor is append-only
The system SHALL treat the backward-adjustment factor as an append-only series, where corporate actions append new factor rows without modifying historical factor rows.

#### Scenario: Historical factor rows are immutable
- **WHEN** a corporate action occurs after some history has been stored
- **THEN** the factor rows for trade dates before the corporate action are not modified
- **AND** only trade dates on or after the corporate action carry the updated factor

#### Scenario: Stored history never expires from upstream factor revisions
- **WHEN** an upstream data source retroactively revises a historical adjustment factor
- **THEN** the stored factor snapshot for already-stored rows is preserved, and the revision only affects how new factor rows are written going forward
