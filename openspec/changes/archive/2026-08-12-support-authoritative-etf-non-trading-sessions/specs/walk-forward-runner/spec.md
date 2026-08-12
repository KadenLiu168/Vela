## MODIFIED Requirements

### Requirement: Runner prepares provenance before source output
Before enqueueing or starting any source-side OOS backtest, `WalkForwardRunner` SHALL validate every generated candidate, resolve each non-negative lookback, use `TradingCalendar` as the sole window/session axis, generate final windows, and build complete versioned configuration plus status-aware input provenance. Every active ETF MUST have listing metadata, and every required on/after-listing ETF/session MUST resolve from exactly one raw price or authoritative full-day status with valid carry ancestry. Missing candidates, invalid lookback, incomplete calendar, metadata gaps, unexplained session gaps, conflicts, or invalid status evidence MUST fail before source output. Errors SHALL contain deterministic category totals and a bounded sorted ETF/date sample.

#### Scenario: Preflight failure precedes OOS persistence
- **WHEN** configuration or status-aware input provenance cannot be completed
- **THEN** the runner raises before invoking any source-side OOS backtest
- **AND** no source signal, run, curve, benchmark, or child is added

#### Scenario: Confirmed full-day events remain admissible and explicit
- **WHEN** every otherwise missing listed ETF/session has valid authoritative status and carry ancestry
- **THEN** preflight completes with status-backed derived records in provenance
- **AND** every OOS window receives the shared resolved panel and atomic deferral policy

#### Scenario: Unknown gaps remain hard failures
- **WHEN** any listed required ETF/session has neither raw price nor authoritative status
- **THEN** preflight fails even if fetch-time gap detection treated the gap as warning-only

#### Scenario: Durable revalidation observes status drift
- **WHEN** listing or status-aware provenance differs between queued capture and claimed execution
- **THEN** queued-input revalidation fails closed before OOS output
