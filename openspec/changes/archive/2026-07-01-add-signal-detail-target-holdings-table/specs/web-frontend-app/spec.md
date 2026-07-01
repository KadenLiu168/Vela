## MODIFIED Requirements

### Requirement: Signal detail latest signal page
The web frontend SHALL render the Signal Detail page as a read-only latest strategy signal detail view backed by the structured latest signal API.

#### Scenario: Signal detail loads latest signal through shared client
- **WHEN** the Signal Detail route renders
- **THEN** frontend page code uses a latest signal helper from `apps/web/src/api/client.ts`
- **AND** the helper calls `GET /api/strategy-signals/latest`

#### Scenario: Signal detail shows latest signal metadata
- **WHEN** the latest signal API response has `has_signal: true`
- **THEN** the Signal Detail page shows the signal date
- **AND** it shows the config version
- **AND** it shows the result
- **AND** it shows the fallback status
- **AND** it shows the generated timestamp

#### Scenario: Signal detail shows target holdings table
- **WHEN** the latest signal API response has `has_signal: true` and includes positions
- **THEN** the Signal Detail page shows a target holdings table populated from the latest signal API `positions`
- **AND** the table shows each position's exchange, symbol, target weight, rank, score, and fallback status
- **AND** target weight is formatted as a clear percentage without losing meaningful decimal precision
- **AND** score is formatted as a readable decimal value without losing meaningful precision

#### Scenario: Signal detail shows empty target holdings state
- **WHEN** the latest signal API response has `has_signal: true` and includes no positions
- **THEN** the Signal Detail page shows a clear empty holdings state
- **AND** it does not treat the successful latest signal response as a request failure

#### Scenario: Signal detail shows empty latest signal state
- **WHEN** the latest signal API response has `has_signal: false`
- **THEN** the Signal Detail page shows a clear empty state explaining that no successful signal exists yet
- **AND** it does not treat the successful empty API response as a request failure

#### Scenario: Signal detail omits candidate diagnostics
- **WHEN** the Signal Detail page renders latest signal data
- **THEN** it does not show candidate ranking diagnostics
