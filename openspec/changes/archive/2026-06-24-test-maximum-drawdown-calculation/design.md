## Context

`packages/core/src/vela_core/strategy_equity_curve.py` already exposes `calculate_strategy_maximum_drawdown`, and `packages/core/tests/test_strategy_equity_curve.py` already contains nearby tests for the strategy equity curve metric helpers. COP-73 is a test coverage change for the existing maximum drawdown behavior.

## Goals / Non-Goals

**Goals:**
- Cover monotonically rising, monotonically falling, and recovery-after-drawdown net value curves.
- Verify exact six-decimal maximum drawdown values and peak/trough dates where a drawdown exists.
- Keep tests deterministic and local to the core package.

**Non-Goals:**
- Change the maximum drawdown formula or sign convention.
- Add persistence, CLI, or backtest runner coverage.
- Add new dependencies or reusable test abstractions.

## Decisions

- Add direct unit tests around `calculate_strategy_maximum_drawdown`.
  - Rationale: the acceptance criteria target maximum drawdown calculation itself, so constructing `StrategyEquityCurvePoint` values keeps the tests focused.
  - Alternative considered: test through the backtest runner. That would add unrelated setup and make failures harder to attribute.
- Keep the existing rising-curve test and add only missing explicit curve shapes.
  - Rationale: the current rising coverage already verifies zero drawdown, while falling and recovery curves need clearer regression coverage.

## Risks / Trade-offs

- Existing implementation might already satisfy the new cases -> The change still improves regression confidence without production edits.
- Overlapping tests could become noisy -> Use two focused additions instead of duplicating every existing zero-drawdown case.
