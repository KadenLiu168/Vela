## ADDED Requirements

### Requirement: Trend filter configuration accepted values
The strategy configuration schema SHALL accept `trend_filter.moving_average_days` values from the closed set `{60, 120, 250}` and `trend_filter.price_relation` values from the closed set `{above, below}`. Any value outside these sets SHALL be rejected at load time.

#### Scenario: 120-day above trend filter is accepted
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to `120` and `trend_filter.price_relation` set to `above`
- **THEN** validation succeeds

#### Scenario: 60-day below trend filter is accepted
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to `60` and `trend_filter.price_relation` set to `below`
- **THEN** validation succeeds

#### Scenario: 250-day above trend filter is accepted
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to `250` and `trend_filter.price_relation` set to `above`
- **THEN** validation succeeds

#### Scenario: Unsupported moving average window is rejected
- **WHEN** backend code validates a strategy configuration with `trend_filter.moving_average_days` set to a value other than `60`, `120`, or `250` (for example `30`)
- **THEN** validation fails

#### Scenario: Unsupported price relation is rejected
- **WHEN** backend code validates a strategy configuration with `trend_filter.price_relation` set to a value other than `above` or `below` (for example `near`)
- **THEN** validation fails
