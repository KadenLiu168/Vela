## ADDED Requirements

### Requirement: Shared frontend value formatting
The web frontend SHALL centralize reusable formatting for displayed numbers, dates, percentages, Decimal strings, and nullable values instead of duplicating page-local implementations.

#### Scenario: Pages reuse shared formatters
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders API-provided numeric, date, percentage, Decimal string, or nullable values
- **THEN** page code uses shared frontend formatter helpers for those value displays
- **AND** page-local formatting helpers are limited to page-specific composition that calls the shared helpers

### Requirement: Consistent research value display
The web frontend SHALL display backtest metrics, target weights, scores, dates, and nullable values consistently across research workflow pages.

#### Scenario: Backtest metric percentages are formatted consistently
- **WHEN** Dashboard or Backtest Detail renders total return, annualized return, maximum drawdown, or volatility from Decimal ratio strings
- **THEN** each finite value is displayed as a percentage with two fractional digits
- **AND** each null metric is displayed as `n/a`

#### Scenario: Signal target weights and scores are formatted consistently
- **WHEN** Signal Detail renders target holding rows from Decimal string values
- **THEN** target weights are displayed as percentages without unnecessary trailing zeroes
- **AND** scores are displayed as decimal values without unnecessary trailing zeroes
- **AND** null rank or score values are displayed as `n/a`

#### Scenario: Dates and nullable metadata are explicit
- **WHEN** Dashboard, Signal Detail, or Backtest Detail renders API-provided date fields or nullable metadata
- **THEN** date values are displayed in a consistent `YYYY-MM-DD` form when the API value is an ISO date or timestamp string
- **AND** nullable metadata values are displayed as `n/a` when absent
