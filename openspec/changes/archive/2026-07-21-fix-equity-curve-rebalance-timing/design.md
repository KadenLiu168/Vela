## Context

`calculate_portfolio_holdings` treats `signal_date` as an as-of close: a signal dated T is excluded from the T snapshot and first appears in the next requested trading-date snapshot. `calculate_strategy_equity_curve`, however, calculates point `i` from the adjusted closing-price ratio between dates `i-1` and `i` while weighting that entire interval with snapshot `i`. A target allocation first available at the end of the interval therefore receives a return that occurred before it became effective.

The mismatch was exposed by the existing rebalance regression fixture. On 2026-06-25 the snapshot changes from SPY 60% / QQQ 40% to QQQ 100%. The current calculation discards SPY's -50% move over 06-24 to 06-25 and reports QQQ's +10% alone, producing `1.122000`; attributing that close-to-close interval to the prior snapshot produces a -26% daily return and `0.754800`.

The calculation has adjusted close prices but no execution ledger, share quantities, adjusted opening-price abstraction, or intraday cash state. The fix must therefore make the existing close-to-close approximation internally consistent without expanding it into an execution simulator.

## Goals / Non-Goals

**Goals:**

- Remove the one-interval look-ahead from rebalance return attribution.
- Establish one unambiguous index contract for equity points, holding snapshots, prices, and turnover.
- Preserve T+1 signal selection and the existing entry/rebalance transaction-cost convention.
- Replace tests that protect the biased result and cover both the interval ending at a rebalance and the following interval.
- Make the limitation of existing persisted backtest results explicit without expanding the persistence or API contract.

**Non-Goals:**

- Change `calculate_portfolio_holdings` or add another signal delay.
- Model orders, shares, cash drift, slippage, market impact, or broker execution.
- Implement open-price execution or split a day into overnight and intraday return segments.
- Change missing-price neutrality, adjusted-price selection, daily quantization, turnover definition, public interfaces, or database schemas.
- Add calculation-version, stale-status, or replacement links to persisted backtest rows; automatically delete, mutate, or regenerate historical rows.

## Decisions

### D1. Attribute each close-to-close interval to the prior snapshot

For every point `i > 0`, use:

```text
interval              = [trading_dates[i-1] close, trading_dates[i] close]
market-return weights = holding_snapshots[i-1].holdings
turnover               = |holding_snapshots[i] - holding_snapshots[i-1]|
curve-point date       = trading_dates[i]
```

This makes the first snapshot the portfolio held after the initial curve close and before the second curve close. A snapshot change recorded at date `i` affects market return beginning with interval `[i, i+1]`, not the interval ending at `i`.

The implementation remains surgical: `_calculate_daily_return` continues receiving both snapshots, but its market-return loop uses `previous_snapshot.holdings`. Price lookup still uses `previous_date` and `snapshot.trade_date`, and turnover still compares the two snapshots.

Alternative considered: delay snapshots by another trading date. Rejected because the holdings layer already correctly maps an as-of T signal to its T+1-effective snapshot; adding another delay would corrupt holdings persistence and duplicate timing logic.

### D2. Preserve transaction costs at the snapshot transition

At point `i`, deduct `turnover(previous_snapshot, snapshot) * transaction_cost_rate` from the same daily return that closes at date `i`. This preserves current behavior for initial entry and rebalance costs:

- empty previous snapshot to populated current snapshot charges entry cost;
- changed target weights charge the sum of absolute weight changes;
- unchanged snapshots charge zero.

Market return and transaction cost intentionally use different aspects of the boundary: the old snapshot earns the interval, then the transition to the new snapshot incurs cost at its effective-date point. This is the minimal coherent close-execution approximation supported by current data.

Alternative considered: move cost to point `i+1`. Rejected because it would separate cost from the transition that creates it, omit a final-date rebalance cost, and break the established transaction-cost contract without improving execution fidelity.

### D3. Do not claim T+1-open execution from close-to-close prices

A true T+1-open model would require the old portfolio to earn previous-close-to-current-open return, the new portfolio to earn current-open-to-current-close return, and both segments to be compounded around an opening rebalance. The current `strategy_price` abstraction exposes only adjusted close, so weighting the full previous-close-to-current-close ratio with the new snapshot is not a valid approximation of open execution.

The change therefore standardizes on close-boundary execution. Adding an adjusted-open abstraction and segmented execution model can be proposed separately if that fidelity becomes necessary.

### D4. Make rebalance regression tests causal

Tests will distinguish three facts rather than infer timing from a single final value:

1. The old allocation earns the interval ending on the date the new snapshot appears.
2. Turnover cost at that boundary is based on old-to-new target changes.
3. The new allocation earns the next complete close-to-close interval.

The existing crash fixture will assert `daily_return=-0.260000` and `net_value=0.754800`. A following trading date will be added where needed to prove QQQ 100% starts earning only after the boundary. Transaction-cost fixtures will include complete prices for the prior holdings so their assertions isolate cost instead of relying on missing-price neutrality.

### D5. Preserve historical runs; keep remediation outside this Change

Persisted equity-curve rows produced before this fix contain biased net values, and their derived metrics are not comparable with corrected reruns. `BacktestRun` has neither a calculation-version nor a stale-status field, while the history API returns all runs for a strategy/configuration without such a distinction. The existing normal workflow can create a new run, but cannot label or replace the old one.

This Change therefore leaves persisted runs untouched. Any inspection, stale-result labeling, deletion, or bulk rerun needs an explicitly approved operational scope and, if results must be distinguishable in the product, a separate Change that adds a versioning/status contract through the model, API, and UI. This keeps the timing correction surgical and prevents an irreversible data operation from being hidden in an implementation task.

## Risks / Trade-offs

- **[Historical metrics change materially]** → Existing run records remain visible and are not comparable with corrected reruns; use separately approved operational remediation if they must be labeled, retired, or rerun.
- **[The close-execution approximation is mistaken for a full execution model]** → State the interval contract in the spec, code comments, and regression test names; keep open execution explicitly out of scope.
- **[Tests pass while only checking the rebalance boundary]** → Include a post-boundary interval proving the new allocation begins earning afterward.
- **[Cost tests accidentally exercise missing-price behavior]** → Supply both endpoint prices for every prior holding in transaction-cost fixtures.
- **[A one-line implementation change has broad downstream effects]** → Run the focused equity-curve tests, the complete core suite, static checks, and a representative end-to-end backtest before accepting corrected metrics.

## Migration Plan

1. Update the delta specification and regression tests so the intended interval contract is executable.
2. Change market-return attribution to `previous_snapshot.holdings` while retaining current turnover calculation.
3. Run focused and full verification before deploying.
4. If historical results require remediation, obtain separate operational approval before inspecting, labeling, retiring, or rerunning them; add a versioning/status Change first if the product must distinguish them.
5. Compare a representative corrected backtest rebalance window manually against the weighted-return arithmetic.

Rollback consists of reverting the implementation and specification change. Because this Change does not mutate historical rows, it has no data rollback. Any separately approved reruns or labels need their own rollback plan.

## Open Questions

None. The change intentionally selects the close-to-close model already supported by the available adjusted-price data.
