## Context

`calculate_strategy_equity_curve` already deducts transaction costs from daily returns using turnover between consecutive holding snapshots and `transaction_cost_bps / 10000`. Current tests cover basic entry, rebalance, and zero-cost behavior, but COP-74 asks for broader transaction cost calculation coverage.

## Goals / Non-Goals

**Goals:**

- Add focused pytest coverage for multiple turnover and cost-rate scenarios.
- Verify transaction cost deductions in both `daily_return` and compounded `net_value`.
- Keep the tests close to the existing strategy equity curve test patterns.

**Non-Goals:**

- Change transaction cost calculation semantics.
- Add new APIs, configuration fields, database schema, or dependencies.
- Refactor strategy equity curve or portfolio holdings implementation.

## Decisions

- Use existing in-memory SQLite test helpers because these tests need realistic persisted signals, holdings, and market prices.
- Add explicit scenario tests instead of parametrizing existing tests heavily, keeping each regression case readable and tied to one acceptance criterion.
- Compare exact six-decimal `Decimal` outputs, matching the current calculation contract.

## Risks / Trade-offs

- Test setup is somewhat verbose because it exercises the persisted signal and holding pipeline. Mitigation: reuse existing helpers and keep new scenarios minimal.
- Existing implementation may already pass the new coverage. Mitigation: treat this COP as a regression-test hardening task rather than forcing production changes.
