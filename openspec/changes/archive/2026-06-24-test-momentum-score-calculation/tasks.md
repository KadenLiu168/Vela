## 1. Test Coverage

- [x] 1.1 Add parametrized momentum score tests covering multiple configured short/long window pairs and score weight pairs.
- [x] 1.2 Assert component returns, weighted score, and repeated identical calculation results for each covered combination.

## 2. Implementation Fixes

- [x] 2.1 Keep production momentum scoring unchanged unless the new tests expose an incorrect calculation.
- [x] 2.2 If a defect is exposed, make the smallest focused fix in momentum scoring.

## 3. Verification

- [x] 3.1 Run the focused momentum scoring tests.
- [x] 3.2 Run `uv run pytest`.
- [x] 3.3 Run the relevant OpenSpec validation command for `test-momentum-score-calculation`.
