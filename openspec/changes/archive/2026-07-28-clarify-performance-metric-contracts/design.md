## Context

`calculate_strategy_annualized_return` computes endpoint CAGR with `365 / elapsed_calendar_days`. `calculate_strategy_volatility` and the corrected `calculate_strategy_sharpe_ratio` summarize `points[1:]` as trading-session observations using `sqrt(252)`; Sharpe subtracts `risk_free_rate / 252` before taking the arithmetic mean. These formulas are individually coherent, but the shared `annualized_return` name and generic Web labels do not disclose the distinct concepts. Some repository audit text still describes the pre-`dea875f5` implementation in which Sharpe was derived from CAGR.

The valid algebraic check for the current Sharpe is based on annualized arithmetic excess return:

`mean(daily_return - risk_free_rate / 252) * 252 / (population_stddev(daily_return) * sqrt(252))`.

CAGR is a geometric endpoint measure and is not an input to this identity.

## Goals / Non-Goals

**Goals:**

- Make the existing metric meanings explicit in specs, tests, documentation, and Web labels.
- Lock the valid Sharpe identity to the same effective observations, risk-free conversion, population dispersion, and 252 factor used by the implementation.
- Prove with a controlled return path that CAGR is not expected to reproduce Sharpe.
- Preserve every current numeric result and external data contract.

**Non-Goals:**

- Change CAGR to a trading-observation formula or volatility to a calendar-day formula.
- Add a reported or persisted arithmetic annualized-return field.
- Change the configured risk-free-rate interpretation.
- Recalculate historical runs or add metric-version metadata.
- Address missing or irregular trading intervals; that belongs to `enforce-equity-curve-trading-interval-integrity`.

## Decisions

### 1. Preserve distinct standard annualization semantics

CAGR remains `(end / start) ** (365 / elapsed_calendar_days) - 1`. Volatility remains population daily-return standard deviation multiplied by `sqrt(252)`. Sharpe remains mean daily excess return divided by its population standard deviation and multiplied by `sqrt(252)`.

Changing CAGR to `252 / observation_count` was rejected because it creates a non-standard trading-observation CAGR and still cannot equal an arithmetic-return Sharpe numerator. Changing volatility to `sqrt(365)` was rejected because its observations are trading sessions. A dynamic observed-sessions-per-year factor was rejected because it makes metric definitions vary between runs and can hide incomplete data.

### 2. Make the valid Sharpe numerator a test-only derived quantity

Focused backend tests will use one coherent curve whose net values compound the same effective daily returns consumed by volatility and Sharpe. They will derive unquantized annualized arithmetic excess return as `mean(effective_daily_return - risk_free_rate / 252) * 252`, derive unquantized annualized volatility from the same effective observations, and verify their ratio produces the expected Sharpe before the public six-decimal quantization boundary.

No public result type or helper is added. The production calculators already use the required observations and formulas; introducing a public metric solely for a sanity check would expand the API without a reporting requirement. A small private helper is permitted only if implementation reveals unavoidable duplicated-moment drift, and it MUST NOT alter numerical outputs.

### 3. Treat CAGR-versus-Sharpe divergence as expected behavior

A controlled non-zero-volatility return path will lock both the CAGR and daily-return Sharpe results and assert that `(CAGR - risk_free_rate) / annualized_volatility` is not the Sharpe contract. This prevents a future refactor from reintroducing the superseded CAGR-based formula.

### 4. Clarify labels without changing payload names

The Backtest Detail metric cards and the Dashboard's completed-run operation summary will use visible labels that communicate:

- `CAGR (calendar-time)`
- `Annualized volatility (252D)`
- `Sharpe (daily returns, 252D)`

The Dashboard's latest-backtest summary currently exposes only Sharpe; that label will also be `Sharpe (daily returns, 252D)`. These are the only current Web surfaces that render the affected backtest metrics.

The REST/TypeScript field `annualized_return`, database column, CLI result attribute, and public Python result types remain unchanged. Renaming them would create compatibility and migration work without improving the calculation.

### 5. Correct only statements that describe the current contracts

Implementation work will search architecture and quantitative-review documents for claims that current Sharpe equals `(CAGR - risk_free_rate) / volatility` or is inflated by mixing 365 and 252. Those claims will be corrected to distinguish the historical bug from current behavior. Unrelated audit findings and historical archived Change artifacts remain untouched.

## Risks / Trade-offs

- **[Longer labels can pressure compact layouts]** → Keep normal wrapping and verify the rendered Backtest Detail and both Dashboard summaries at the existing mobile and desktop breakpoints.
- **[Users may still divide displayed rounded values]** → Document that the exact identity uses arithmetic excess return and unquantized moments; do not promise equality from independently rounded display values.
- **[Documentation edits can erase historical context]** → Correct current-state assertions while retaining explicit wording that the prior CAGR-based Sharpe implementation was superseded.
- **[A refactor could change numeric outputs accidentally]** → Capture current hand-derived CAGR, volatility, and Sharpe vectors before any optional private-helper refactor and require exact six-decimal preservation.

## Migration Plan

No data migration is required. Deploy backend tests/documentation and Web label changes together. Rollback restores the prior labels and documentation; metric values and stored data are identical in either direction.

## Open Questions

None.
