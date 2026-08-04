## 1. Typed evidence contracts and focused tests

- [x] 1.1 Add failing report tests for five metric summaries with metric-local null handling, zero-valid samples, valid/total counts, `sufficient` versus `insufficient_evidence`, and negative maximum-drawdown worst-value labeling.
- [x] 1.2 Add failing tests for positive-window rates, per-benchmark win rates, ties, zero denominators, relative-return/CAGR standard summaries, and explicit numerators/denominators/counts/status.
- [x] 1.3 Add failing tests for `train_sharpe - oos_sharpe` summaries and per-parameter validated-config canonical frequencies, adjacent transition counts and transition rates.
- [x] 1.4 Extend typed Walk-forward window/summary result structures and pure aggregation helpers until the focused evidence tests pass.

## 2. Runner and terminal evidence report

- [x] 2.1 Add failing runner tests requiring selected OOS total return and volatility to be copied alongside CAGR, Sharpe and maximum drawdown without changing benchmark execution or source transaction ownership.
- [x] 2.2 Update the runner mapping and all test/result constructors to provide the complete five-metric OOS evidence.
- [x] 2.3 Add failing formatter tests for counts, evidence status, positive and benchmark-win rates, generalization gaps, parameter transitions, and the absence of pass/fail or continuous-curve claims.
- [x] 2.4 Update the terminal formatter to render the complete evidence contract, label the deepest negative drawdown as worst, and retain per-window isolation.

## 3. Production-path integration contract

- [x] 3.1 Build an Alembic-prepared file-backed SQLite fixture with one active `SSE:510300`, a minimal valid ETF universe, and complete official sessions/prices from the maximum candidate lookback envelope through deterministic Walk-forward windows.
- [x] 3.2 Execute the real `WalkForwardRunner` and `run_backtest` path without metric mocks; assert literal per-window five-metric values, representative aggregate/generalization/dual-benchmark values, exact counts/rates, deterministic OOS identities and parameter stability.
- [x] 3.3 Add CLI managed-session failure coverage proving a later OOS or fixed-benchmark failure rolls back signals, positions, runs, strategy curves, benchmarks and benchmark curves and never writes to the default `vela.db`.

## 4. Validation

- [x] 4.1 Run the focused Walk-forward report, runner, integration and CLI tests and correct only regressions caused by this Change.
- [x] 4.2 Run `openspec validate strengthen-walk-forward-evaluation-contract --strict` and trace every requirement and scenario to its implementation task and test.
- [x] 4.3 After the final Python revision, run the complete Python CI-equivalent gate from the repository root and record the results for review.
