## Context

`StrategyConfig` and `load_strategy_config()` already enforce the v1 strategy configuration contract. Existing tests cover many valid and invalid cases, but several direct schema-validation tests only assert that `ValidationError` is raised. COP-67 asks for test coverage across valid and invalid strategy configs and assertable validation failure messages.

## Goals / Non-Goals

**Goals:**

- Add narrow pytest coverage for representative valid and invalid strategy configuration inputs.
- Assert error messages for direct Pydantic validation and loader-wrapped `ConfigError` failures.
- Keep the current strategy configuration schema, loader API, and checked-in YAML shape unchanged.

**Non-Goals:**

- Redesign strategy configuration fields or introduce a new config version.
- Change ETF pool validation, signal generation, or backtesting behavior.
- Add new dependencies or testing frameworks.

## Decisions

1. Extend the existing `packages/core/tests/test_strategy_config.py` coverage instead of adding a new test module.

   Rationale: The existing file already owns strategy configuration validation tests and local fixtures. Keeping COP-67 there avoids duplicate helpers and keeps the change surgical.

2. Assert representative validation messages rather than every Pydantic message for every invalid permutation.

   Rationale: COP-67 requires failure information to be assertable. Checking field paths and custom validator messages on representative cases proves the contract without over-coupling tests to every generated Pydantic wording.

3. Treat implementation changes as out of scope unless a test exposes a mismatch.

   Rationale: Existing runtime validation already satisfies the known strategy configuration rules. This COP is in the testing milestone and should not alter behavior speculatively.

## Risks / Trade-offs

- Pydantic default message wording can change across major versions -> Prefer assertions against stable field paths and project-owned custom validator messages where practical.
- Narrow message assertions may miss an untested invalid case -> Keep existing invalid input coverage and add the missing message-focused checks required by COP-67.
