## Context

`calculate_portfolio_holdings` produces one target-allocation snapshot for every requested trading date. Between strategy signals, those snapshots carry the same `strategy_signal_id` and target weights. `calculate_strategy_equity_curve` currently multiplies every interval return by the prior snapshot's target weights, so a weekly or monthly target is implicitly restored at every close even though no new signal or transaction exists.

The earlier rebalance-timing correction established a close-boundary contract: the actual portfolio held at the interval start earns `[T-1 close, T close]`, then a snapshot transition at T incurs turnover and becomes effective for the following interval. This Change must preserve that ordering while replacing target-weight carry-forward with a persistent economic holding state.

Vela does not have an order ledger, integer share sizing, adjusted open prices, corporate-action share events, or intraday cash. Net-value returns do have a canonical total-return view: each interval uses `forward_adjusted_prices()` anchored at its current date. A literal broker-share simulator would therefore add unsupported execution semantics. A normalized position-value ledger is the smallest state that is economically equivalent to fractional shares under the current total-return and close-execution assumptions.

Persisted `BacktestEquityCurve` rows already expose `cash`, `market_value`, `total_assets`, and `positions_json`, but the runner currently derives them from target holdings rather than from equity calculation state. Once actual weights drift, that derivation would contradict the calculated net value unless the same state flows into persistence.

## Goals / Non-Goals

**Goals:**

- Carry normalized per-ETF market values and cash across trading dates without implicit daily rebalancing.
- Attribute every close-to-close interval to the actual economic holdings at its start.
- Detect a rebalance from a changed `strategy_signal_id`, including a new signal whose target weights equal the preceding signal's targets.
- Calculate turnover from pre-trade actual weights to normalized target weights and compound transaction costs after market return.
- Preserve high-precision internal Decimal state and quantize only observable curve and persistence outputs.
- Persist cash, market value, total assets, target weights, and actual weights from the same calculated state.
- Identify new results with `equity_model_version: "drift_v1"` without a database migration.
- Keep historical rows immutable and make no persistent regeneration part of implementation or validation.

**Non-Goals:**

- Model orders, integer shares, lot sizes, bid/ask spread, slippage, market impact, tax, or broker execution.
- Add open-price or intraday execution segments.
- Change signal generation, signal scoping, T+1 effectiveness, strategy selection, or rebalance-date generation.
- Change the per-interval forward-adjusted total-return contract.
- Distinguish a legitimate suspension from corrupt missing market data or introduce a tradability model.
- Pay interest on cash or support leveraged/short target allocations.
- Add or migrate database columns.
- Mutate, delete, label, or automatically rerun historical backtests.

## Decisions

### D1. Carry normalized position values and cash as the authoritative state

For each curve date, the calculation carries:

```text
PortfolioState
  active_signal_id
  cash_value
  position_values[etf_id]
```

`position_values` and `cash_value` use the same normalized unit as net value. Actual weights are derived as `position_value / total_assets`; they are outputs, not the primary mutable state.

For each interval `[T-1, T]`, every existing position value is multiplied by its canonical forward-adjusted price ratio. Cash remains unchanged. If a held ETF lacks either endpoint price, its multiplier is `1`, preserving the current missing-price-neutral contract without deleting the holding from state.

This value ledger is preferred over:

- **Mutable actual weights only**: mathematically sufficient for simple returns, but it cannot directly produce auditable cash and market values and makes conservation checks indirect.
- **Literal ETF shares and an order ledger**: more realistic only if execution prices, corporate actions, lots, and tradeability are also modeled; those inputs do not exist.

### D2. Initialize the first curve point as a post-initialization baseline

The first point retains `net_value=1.000000` and `daily_return=0.000000`. Its state is initialized from the first effective snapshot:

- an empty snapshot becomes cash `1`;
- a populated snapshot becomes normalized target holdings with residual cash;
- no initial-entry cost is charged at the first point.

This preserves the existing initial-point contract. A transition from an empty first snapshot to a later populated snapshot remains a normal entry rebalance and incurs cost on that later date.

Non-empty target weights produced by current strategies are intended to be fully invested but can sum infinitesimally above or below one because `Decimal("1") / N` repeats. Execution allocation weights are therefore normalized by their positive sum at a rebalance. The original `target_weight` values remain unchanged in signal and persisted target metadata. Empty targets mean 100% cash. Partial-cash, leveraged, negative, or zero-sum non-empty targets remain outside this Change.

### D3. A new signal identity, not a weight comparison, triggers rebalance

A rebalance occurs at T exactly when:

```text
snapshot_T.strategy_signal_id != state.active_signal_id
```

The old state first earns the interval ending at T. The calculation then compares pre-trade actual risky-asset weights with the normalized target allocation carried by `snapshot_T`.

This means two consecutive signals with identical 50/50 targets still trade back to 50/50 if market movement has drifted the portfolio to 55/45. Consecutive daily snapshots carrying the same signal do not trade, even though their target metadata is repeated.

This is preferred over comparing target maps because target equality does not imply that no executed rebalance is required.

### D4. Compute turnover from pre-trade actual exposure

At a signal transition, with pre-trade total assets `V_pre`:

```text
actual_weight_i = position_value_i / V_pre
target_weight_i = raw_target_weight_i / sum(raw_target_weights)
turnover         = Σ_i |target_weight_i - actual_weight_i|
cost             = V_pre × turnover × transaction_cost_rate
V_post           = V_pre - cost
```

The union of actual and target ETF ids is used, so entry, exit, replacement, and same-target recentering are covered. Cash is the residual asset and is not added as a second turnover leg; switching one fully invested ETF to another still has turnover `2` because the risky sell and risky buy are both counted.

After cost, position values are reset to `V_post × target_weight_i` and cash is the residual. This retains Vela's existing weight-turnover cost abstraction. Solving broker-exact traded notional after fees would require a different execution model and is not introduced here.

If pre-trade total assets are non-positive, the calculation cannot derive finite weights or continue a meaningful long-only curve and SHALL fail explicitly rather than divide by zero or fabricate a recovery.

### D5. Compound market return and transaction cost in event order

Because positions earn market return before the close-boundary rebalance:

```text
gross_growth = V_pre / V_previous
net_growth   = gross_growth × (1 - turnover × transaction_cost_rate)
daily_return = V_post / V_previous - 1
```

The existing additive approximation,

```text
market_return - turnover × transaction_cost_rate
```

omits the interaction between the day's market move and a cost charged on closing pre-trade assets. Multiplicative sequencing makes the curve consistent with the established event order.

### D6. Keep internal state unquantized and quantize only observable output

Position values, cash, weights, turnover, and net asset values remain at Decimal working precision while the loop advances. Six-decimal quantization is applied only when constructing externally observable curve fields and persisted numeric/JSON values.

The next interval must consume the unquantized state rather than reconstructing state from the previous persisted point. This prevents daily rounding from becoming an additional artificial rebalance or compounding drift.

At the output boundary, aggregate values are reconciled so:

```text
cash + market_value = total_assets = net_value
```

at the persisted six-decimal precision.

### D7. Carry actual state on equity points and persist it directly

The equity calculation will expose enough immutable per-date state for the runner to persist without independently recalculating holdings:

- normalized cash value;
- aggregate market value;
- each held ETF id;
- the current signal target weight, when present;
- the actual post-close/post-rebalance weight.

`StrategyEquityCurvePoint` is publicly exported and is directly constructed by metric-only callers and tests using its existing `trade_date`, `net_value`, and `daily_return` fields. Preserve that construction contract by adding one optional immutable portfolio-state payload rather than making several new state fields mandatory. `calculate_strategy_equity_curve` SHALL populate the payload on every returned point. The runner SHALL require it and fail explicitly if a caller supplies a point without calculated state, so compatibility defaults can never be persisted as fabricated cash or positions.

The public metric calculators continue to consume `trade_date`, `net_value`, and `daily_return`; they do not recalculate weights.

`positions_json` remains a JSON list and retains `etf_id` and `target_weight`. Each entry adds `actual_weight`. No relational schema migration is required. The runner uses the calculated point state for `cash`, `market_value`, `total_assets`, and `positions_json`, removing its second, target-only interpretation of the portfolio.

Alternative considered: leave persisted curve rows target-only. Rejected because the stored cash and holdings would contradict the drift-based net value and could not be audited.

### D8. Version the calculation semantics in run parameters

Every newly persisted run adds:

```json
{"equity_model_version": "drift_v1"}
```

to `parameters_json`. Strategy identity and configuration version continue to identify strategy behavior; the equity model version identifies shared backtest-engine semantics.

Adding a database column and API/UI stale-state workflow is not required for this Change. Historical rows remain readable and unchanged, but rows without `equity_model_version` must not be treated as directly comparable with `drift_v1` results.

### D9. Preserve shared price input and missing-price semantics

The equity curve continues consuming the exact `price_panel` already loaded for the backtest data snapshot. Each held ETF interval is projected with `forward_adjusted_prices([previous_row, current_row], rebalance_date=current_date)`.

When either price row is absent, the position value is carried unchanged. This is equivalent to the current zero-return rule and avoids broadening the Change into gap classification or tradeability. The existing gap warnings and strict systematic-gap behavior remain unchanged.

## Risks / Trade-offs

- **[Historical metrics and walk-forward rankings change]** → Record `drift_v1`, keep old rows immutable, and validate parameter-ranking behavior on temporary databases only.
- **[Actual-weight persistence is mistaken for broker execution]** → Name fields as normalized market values/weights and keep shares, orders, fills, lots, and slippage explicitly out of scope.
- **[Repeated target weights hide a real rebalance]** → Use `strategy_signal_id` transitions and add a same-target/new-signal regression.
- **[Decimal thirds create tiny negative cash or phantom turnover]** → Normalize positive target weights at the execution boundary and test three-way allocations.
- **[Daily six-place rounding compounds into material drift]** → Maintain unquantized internal state and test a long multi-day path against an independent high-precision calculation.
- **[Missing held-asset prices conceal bad data]** → Preserve the current neutral rule for compatibility, retain warnings, and leave suspension-versus-corruption handling to a separate Change.
- **[Cost rate times turnover reaches or exceeds one]** → Reject a non-positive post-cost portfolio explicitly; do not continue with negative normalized assets.
- **[Runner and calculator diverge]** → Persist state carried by equity points and remove target-only state reconstruction from the runner.
- **[Public metric-only point construction breaks]** → Add one optional state payload, require the calculator to populate it, require the runner to reject its absence, and keep metric functions dependent only on the existing three fields.

## Migration Plan

1. Add executable regression tests for drift, signal-identity rebalance, multiplicative costs, precision, and persisted-state conservation.
2. Introduce the normalized portfolio state inside the equity calculation while preserving T+1 and per-interval price projection.
3. Expose actual state on curve points and update the runner to persist that same state.
4. Add `equity_model_version: "drift_v1"` to new backtest parameters.
5. Run focused core tests, the complete core suite, static checks, strict OpenSpec validation, and representative backtest/walk-forward tests against isolated temporary databases.
6. Do not run against or regenerate persistent `vela.db` without a separate explicit authorization.

Rollback is a code/spec revert. No schema rollback and no data rollback are required because implementation does not mutate existing results. Any separately authorized regenerated runs remain distinct immutable rows and require their own operational rollback decision.

## Open Questions

None. This Change intentionally selects normalized value accounting as the current close-based fractional-holding model and defers broker-execution fidelity.
