## Context

`select_with_defensive_fallback` already returns the configured defensive asset when ranked ETF candidates cannot satisfy `selection.top_n`, and returns Top N selections when enough ranked candidates exist. COP-71 is a test-hardening change for that behavior.

## Goals / Non-Goals

**Goals:**
- Verify fallback selection for the no-ranked-candidates boundary.
- Keep sufficient-ranked-candidates behavior covered so the defensive asset is not selected when fallback should not trigger.
- Verify defensive asset identity and target weight output.

**Non-Goals:**
- Change production fallback, ranking, scoring, or Top N selection behavior.
- Change persistence, CLI behavior, configuration, or database schema.

## Decisions

- Add focused unit coverage in `packages/core/tests/test_momentum_scoring.py`.
  - Rationale: fallback selection is pure business logic and already has local test helpers for strategy config and rankings.
  - Alternative considered: add integration coverage through signal generation. Existing signal-generation tests already cover persistence fallback, while COP-71 targets selection fallback output directly.

## Risks / Trade-offs

- Existing broad insufficient-candidates coverage may overlap with the new no-ranked-candidates test -> Keep the new test focused on the empty ranking boundary so it adds a distinct fallback trigger case.
