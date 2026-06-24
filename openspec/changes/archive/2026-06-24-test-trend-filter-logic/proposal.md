## Why

COP-70 requires explicit test coverage for ETF trend filter logic across passing, failing, and boundary cases. The existing trend-filtering behavior is specified, but the test suite should make the filter contract easier to verify before later strategy signal work depends on it further.

## What Changes

- Add focused tests that verify an ETF passes only when current strategy price is strictly above the 120-day moving average.
- Add coverage where a passing ETF and a failing ETF are evaluated in the same test setup.
- Keep equality, below-average, missing-current-price, and missing-moving-average cases covered as boundary behavior.
- Do not change production trend filter behavior unless the new tests expose an implementation defect.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `trend-filtering`: Clarify test coverage for the existing trend filter calculation contract without changing the runtime requirement.

## Impact

- Affected tests: `packages/core/tests/test_trend_filter.py`.
- Affected code: none expected.
- Affected dependencies, APIs, and database schema: none.
