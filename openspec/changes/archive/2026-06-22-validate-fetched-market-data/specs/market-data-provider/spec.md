## ADDED Requirements

### Requirement: AkShare fetched daily price validation
The system SHALL validate AkShare ETF daily rows before returning internal `DailyPrice` values.

#### Scenario: Reject missing required row values
- **WHEN** AkShare returns an ETF daily row with a missing, null, or empty required date, OHLC price, or volume value
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid trade date
- **WHEN** AkShare returns an ETF daily row with a trade date that cannot be parsed as a calendar date
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid OHLC price
- **WHEN** AkShare returns an ETF daily row with an OHLC price that is non-numeric, non-finite, or less than or equal to zero
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject inconsistent OHLC relationship
- **WHEN** AkShare returns an ETF daily row whose high price is lower than open, low, or close, or whose low price is higher than open, high, or close
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Reject invalid volume
- **WHEN** AkShare returns an ETF daily row with a volume that is non-numeric, non-integral, or negative
- **THEN** the provider raises a provider-level error instead of returning `DailyPrice` values

#### Scenario: Include source row context in validation failure
- **WHEN** AkShare row validation fails
- **THEN** the provider-level error includes source, symbol, requested date range, row index, failing column or field, invalid value, and validation reason where applicable

#### Scenario: Reject whole result when one row is invalid
- **WHEN** AkShare returns multiple ETF daily rows and any one row fails validation
- **THEN** the provider raises a provider-level error and returns no partial `DailyPrice` results
