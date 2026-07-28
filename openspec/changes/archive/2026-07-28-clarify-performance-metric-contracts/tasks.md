## 1. Lock the backend metric contracts

- [x] 1.1 Add a controlled effective-return test vector whose net values compound those same returns, with hand-derived calendar-time CAGR, 252D population volatility, annualized arithmetic excess return, and daily-return Sharpe expectations.
- [x] 1.2 Add a regression assertion that the valid unquantized arithmetic-excess-return/annualized-volatility identity produces the expected six-decimal Sharpe.
- [x] 1.3 Add a counterexample proving `(CAGR - risk_free_rate) / annualized_volatility` is not the Sharpe contract while preserving all existing metric results and public signatures.
- [x] 1.4 Introduce a private shared-moment helper only if the tests expose duplicated calculation drift; otherwise leave the production backend formulas unchanged.

## 2. Clarify Web metric labels

- [x] 2.1 Update focused tests for the Backtest Detail metric cards, Dashboard completed-run operation summary, and Dashboard latest-backtest summary to require each applicable clarified label while retaining current value/null formatting.
- [x] 2.2 Update those three Web metric surfaces to render `CAGR (calendar-time)`, `Annualized volatility (252D)`, and/or `Sharpe (daily returns, 252D)` as applicable, without deriving or changing any metric value.
- [x] 2.3 Run focused rendered tests for accessible labels and browser QA at the existing mobile and desktop breakpoints; confirm the longer labels wrap without clipping, overflow, or duplicate-label regressions.

## 3. Correct current-state documentation

- [x] 3.1 Search non-archived architecture and quantitative-review documents for claims that current Sharpe is derived from CAGR or mixes 365 and 252 inside one ratio.
- [x] 3.2 Correct only stale current-state claims, preserve explicit historical context, and document the valid arithmetic excess-return sanity check.

## 4. Validate compatibility and completion

- [x] 4.1 Run focused core metric tests and prove exact six-decimal CAGR, volatility, and Sharpe outputs are unchanged.
- [x] 4.2 Run focused Web tests plus frontend lint, stylelint, typecheck, and build.
- [x] 4.3 Run the complete Python test/lint/format/typecheck gates, `git diff --check`, and strict validation for this Change.
- [x] 4.4 Trace every requirement and scenario to implementation/test evidence and confirm there are no API, database, configuration, or historical-data changes.
