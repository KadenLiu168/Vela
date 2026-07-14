## MODIFIED Requirements

### Requirement: Generate strategy signal from local market data

The system SHALL generate a strategy signal for a requested signal date using the active ETFs and the strategy configuration supplied by the caller, plus a price panel mapping already loaded for the relevant trading-date window. The signal generation function SHALL NOT accept a database session and SHALL NOT issue `MarketPrice` queries during generation.

#### Scenario: Generate ranked strategy signal from injected inputs
- **WHEN** backend code generates a strategy signal for a date with a non-empty active ETF list, a price panel covering the longest configured window, and a strategy configuration
- **THEN** the function reads only from the injected inputs and the configured `StrategyConfig`
- **AND** the function applies the configured trend filter before ranking eligible ETFs
- **AND** the function calculates configured momentum scores for ETFs that pass the trend filter
- **AND** the function returns the selected target positions with rank, score, and target weight

#### Scenario: Generate signal performs zero MarketPrice queries
- **WHEN** backend code generates a strategy signal for a date through the pure-function entry point
- **THEN** no SQL statement targets the `market_price` table during the call

#### Scenario: Persistence is delegated to the caller via callback
- **WHEN** backend code generates a strategy signal and supplies a persist callback
- **THEN** the function invokes the callback with the generated result
- **AND** the function does not commit, flush, or otherwise write to the database when no callback is supplied

#### Scenario: Apply defensive fallback during generation
- **WHEN** backend code generates a strategy signal and fewer eligible ranked ETFs exist than the configured Top N
- **THEN** the system returns one target position per configured defensive asset
- **AND** each defensive position has an equal target weight of `1 / N` where `N` is the number of configured defensive assets
- **AND** the sum of the defensive target weights equals `1.0` within Decimal rounding tolerance (each weight is `Decimal("1") / Decimal(N)`; the total is approximately, not exactly, `1.0` for N > 1)
- **AND** each defensive asset id is resolved from the caller-supplied defense lookup without issuing any database query

#### Scenario: Fail when no active ETFs exist
- **WHEN** backend code generates a strategy signal and the caller-supplied active ETF list is empty
- **THEN** the function returns a failed result with a clear error message
- **AND** the function does not raise

#### Scenario: Fail when defensive asset is missing locally
- **WHEN** backend code generates a fallback signal and any configured defensive asset exchange and symbol are not present in the caller-supplied defense lookup
- **THEN** the function returns a failed result with a clear error message
