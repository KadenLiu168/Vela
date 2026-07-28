## Why

Vela reports calendar-time CAGR beside 252-trading-day volatility and Sharpe without explaining that they summarize different return concepts. This makes a mathematically valid metric set look inconsistent and encourages the invalid sanity check `Sharpe ≈ (CAGR - risk_free_rate) / volatility`, even though Sharpe is calculated from arithmetic daily excess returns.

## What Changes

- Preserve the existing numerical contracts: CAGR remains compounded over elapsed calendar days, while volatility and Sharpe remain annualized from effective daily return observations using 252 trading days.
- Define the valid Sharpe consistency identity against annualized arithmetic excess return and annualized volatility, calculated from the same unquantized effective-return moments.
- Add regression coverage proving the valid identity and proving that CAGR is not the Sharpe numerator.
- Clarify backend documentation and correct stale audit text that still describes the superseded CAGR-based Sharpe implementation.
- Clarify Web labels so users can distinguish calendar-time CAGR from 252-trading-day volatility and daily-return Sharpe.
- Keep public Python signatures, REST/CLI payloads, database columns, persisted metric values, and historical runs unchanged.

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `strategy-equity-curve`: Clarify the distinct annualization contracts and require regression coverage for the correct arithmetic-excess-return Sharpe identity.
- `web-frontend-app`: Require backtest metric labels to disclose the calendar-time versus 252-trading-day conventions.

## Impact

- Affected code and tests: focused metric tests under `packages/core` (with metric internals changed only if a shared private helper proves necessary), plus backtest metric labels and tests under `apps/web`.
- Affected documentation: OpenSpec metric contracts and stale architecture/quant review statements that imply current Sharpe is derived from CAGR.
- Compatibility: no API, schema, configuration, persistence, or historical-data migration; existing numerical CAGR, volatility, and Sharpe results remain unchanged.
