## 1. Add failing interval-integrity tests

- [x] 1.1 Add runner tests proving requested dates come from ordered `TradingCalendar` rows rather than the stored-price union.
- [x] 1.2 Add tests for exact trading-session lookback selection, including an unrelated missing date outside the required set.
- [x] 1.3 Add preflight failure tests for missing requested/lookback calendar coverage, a systematic price gap, and one active-universe ETF/date gap.
- [x] 1.4 Add inception-boundary tests proving pre-inception dates are exempt, the ETF joins the candidate universe on the first signal date on or after inception, stored pre-inception rows are excluded from strategy-visible history, post-inception dates are mandatory, and absent inception metadata does not suppress truncated history.
- [x] 1.5 Assert every preflight failure identifies actionable date/ETF context and leaves no new strategy signal, backtest run, equity row, or signal link.
- [x] 1.6 Replace missing-price carry tests with direct equity-calculator tests that independently omit the previous and current endpoint price for a held ETF and require explicit failure.
- [x] 1.7 Add a complete controlled-dataset regression locking existing signals, T+1 holdings, equity values, transaction costs, CAGR, volatility, Sharpe, and persistence linkage.

## 2. Make the trading calendar authoritative

- [x] 2.1 Replace stored-price-union trading-date resolution with inclusive ordered `TradingCalendar` resolution and fail when requested coverage is unavailable.
- [x] 2.2 Resolve the exact preceding official sessions required by `resolve_strategy(config).lookback_days()` instead of defining completeness with the approximate `max_window * 2 + 10` calendar buffer; a containing panel load may remain for query/snapshot purposes but must not expand the required set.
- [x] 2.3 Load the containing price panel and validate every exact required `(active_etf_id, trade_date)` on or after the ETF's declared inception date, using the lookback start when inception metadata is absent.
- [x] 2.4 Produce deterministic bounded errors containing total gap count plus sorted representative ETF/date gaps, and run validation before historical signal generation invokes its persistence callback.
- [x] 2.5 Filter both the active ETF collection and each ETF's strategy-visible price history for every historical signal calculation: require `inception_date <= signal_date`, remove rows before a declared inception, and treat absent inception metadata as already eligible.

## 3. Enforce held-position endpoint prices

- [x] 3.1 Change equity mark-to-market behavior to raise when an interval-start holding lacks its previous or current strategy-price row, identifying the ETF and missing endpoint date(s).
- [x] 3.2 Preserve prior-holding interval attribution, post-interval rebalance timing, natural weight drift, forward-adjusted price arithmetic, transaction costs, and empty-cash behavior for complete inputs.
- [x] 3.3 Remove obsolete missing-price value-carry/neutral-return expectations from focused tests without weakening unrelated equity arithmetic coverage.

## 4. Remove obsolete tolerant controls

- [x] 4.1 Remove `BacktestGapDetectionConfig`, the `run_backtest(..., gap_detection=...)` parameter, and the package public export.
- [x] 4.2 Remove CLI strict-data-quality/systematic-gap-threshold options and update CLI wrappers, help tests, and caller tests to the mandatory-validation API.
- [x] 4.3 Update non-archived documentation that describes warning-only backtest gaps or configurable tolerance; leave fetch-time warn-only quality logging unchanged.

## 5. Validate correctness and safety

- [x] 5.1 Run focused core runner, equity-curve, strategy, and CLI tests, including atomic no-write assertions for every failure class.
- [x] 5.2 Run the complete Python test/lint/format/typecheck gates and `git diff --check`.
- [x] 5.3 Run strict validation for this Change and trace every requirement/scenario to implementation and test evidence.
- [x] 5.4 Perform any real-data preflight read-only; if an execution-level check is needed, use a recoverable `/tmp` database copy and never mutate or rebuild the live `vela.db`.
- [x] 5.5 Confirm complete-data metric formulas, public REST/database schemas, transaction ownership, and existing historical rows remain unchanged; document the intentional Python/CLI breaking migration.
