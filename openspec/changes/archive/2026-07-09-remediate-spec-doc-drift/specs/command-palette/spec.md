## MODIFIED Requirements

### Requirement: Palette row model and data sources
The command palette SHALL surface exactly four row kinds, built from these data sources:
- **page** rows: hard-coded list of the three AppShell `navItems` (`/`, `/signals`, `/backtests`).
- **backtest** rows: the result of `listBacktests(10)` (already exposed in `apps/web/src/api/client.ts`).
- **etf** rows: the `etf_list` field on the response of `getDashboard()` (already exposed in `apps/web/src/api/client.ts`).
- **action** rows: the three dashboard actions (Bootstrap local database, Generate strategy signal, Run backtest) bound to the same code paths the Dashboard buttons call today (`bootstrapLocalDatabase`, `generateStrategySignal`, `runBacktest`).

The palette SHALL also surface the latest signal as a single **backtest**-shaped row (or as a dedicated **signal** row kind if the implementation chooses to introduce one), sourced from `getLatestStrategySignal()`.

#### Scenario: Palette fetches data on open
- **WHEN** the palette transitions from closed to open
- **THEN** the palette SHALL issue a `listBacktests(10)` request
- **AND** the palette SHALL issue a `getLatestStrategySignal()` request
- **AND** the palette SHALL issue a `getDashboard()` request
- **AND** all three requests SHALL be issued in parallel (no serial waterfall)
- **AND** until all three have settled, the `data-testid="command-palette-loading"` element SHALL be present

#### Scenario: API failure surfaces a quiet error row
- **WHEN** the palette is open
- **AND** any of `listBacktests`, `getLatestStrategySignal`, or `getDashboard` rejects
- **THEN** the palette SHALL still render the rows it has
- **AND** it SHALL render a `data-testid="command-palette-error"` row whose text mentions which source failed
- **AND** it SHALL NOT throw an unhandled error to the console for the user
