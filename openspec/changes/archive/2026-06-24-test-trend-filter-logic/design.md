## Context

The `trend-filtering` spec already defines the v1 rule: an ETF passes only when its current strategy price is strictly above its 120-trading-day moving average. Existing unit tests cover individual pass, fail, and missing-data cases, while COP-70 asks for explicit confidence that both satisfying and non-satisfying ETFs are handled correctly.

## Goals / Non-Goals

**Goals:**

- Strengthen tests for the existing trend filter contract.
- Verify passing and failing ETFs in the same setup so the filter behavior is easy to audit.
- Preserve boundary coverage for equality, below-average prices, missing current price, and missing moving average.

**Non-Goals:**

- Do not add new trend filter operators or moving-average windows.
- Do not change strategy signal generation, ranking, selection, persistence, or backtesting behavior.
- Do not change production code unless the tests expose a defect in existing behavior.

## Decisions

1. Add focused coverage to `packages/core/tests/test_trend_filter.py`.

   Rationale: COP-70 is about trend filter logic, and this file already owns the direct `apply_trend_filter` contract. Keeping the test close to the unit under test avoids broader strategy signal setup when no integration behavior is being changed.

   Alternative considered: add only a strategy signal generation integration test. That would prove downstream filtering indirectly, but it would make the trend rule harder to diagnose and would overlap with existing signal generation coverage.

2. Treat equality as the primary boundary case.

   Rationale: the existing spec says "above" means strictly greater than the moving average. Equality is the clearest boundary between passing and failing behavior and should remain explicitly asserted.

   Alternative considered: only test above and below. That would miss the strictness of the threshold.

## Risks / Trade-offs

- Test duplication with existing single-case tests -> Mitigation: add one mixed-outcome test that complements the existing focused boundary tests instead of rewriting all coverage.
- Production code change creep -> Mitigation: only edit implementation if the new tests fail because behavior is incorrect.
