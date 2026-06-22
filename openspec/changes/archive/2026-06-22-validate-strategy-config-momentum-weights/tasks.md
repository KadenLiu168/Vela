## 1. Validation Tests

- [x] 1.1 Add tests that reject equal short and long momentum windows.
- [x] 1.2 Add tests that reject a short momentum window greater than the long momentum window.
- [x] 1.3 Add tests that reject zero short or long score weights.
- [x] 1.4 Keep coverage for score weights whose total is not 1.0.

## 2. Schema Implementation

- [x] 2.1 Update `MomentumConfig` to reject configurations where `short_window_days >= long_window_days`.
- [x] 2.2 Update `ScoreWeightsConfig` so `short` and `long` weights must be positive.
- [x] 2.3 Preserve the existing score weight total validation tolerance.

## 3. Verification

- [x] 3.1 Run `uv run pytest packages/core/tests/test_strategy_config.py -q`.
- [x] 3.2 Run `openspec status --change "validate-strategy-config-momentum-weights"` and confirm the change remains apply-ready.
