## ADDED Requirements

### Requirement: AkShare transient source retry
The system SHALL retry transient AkShare source-call failures with a simple finite retry policy before surfacing a provider-level failure.

#### Scenario: Retry temporary AkShare source failure
- **WHEN** the AkShare source call fails temporarily before returning ETF daily rows
- **THEN** the provider retries the source call using a finite retry count and simple wait policy

#### Scenario: Return rows after retry succeeds
- **WHEN** an AkShare source call fails initially but succeeds before retry attempts are exhausted
- **THEN** the provider returns normalized `DailyPrice` values for the successful source response

#### Scenario: Raise provider error after retries are exhausted
- **WHEN** all AkShare source-call retry attempts fail for a requested symbol and date range
- **THEN** the provider raises a provider-level error that includes source, symbol, and date-range context

#### Scenario: Do not retry invalid returned rows
- **WHEN** AkShare returns rows that fail normalization or validation
- **THEN** the provider raises a provider-level error without retrying row normalization or validation

#### Scenario: Preserve fetch log recording for final failure
- **WHEN** an upper-layer market data fetch workflow receives a provider-level error after retry exhaustion
- **THEN** the workflow can record the final failed or partial result in the existing fetch log failure fields
