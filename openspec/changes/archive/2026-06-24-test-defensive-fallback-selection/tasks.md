## 1. Defensive Fallback Tests

- [x] 1.1 Add a focused unit test proving no ranked ETF candidates trigger defensive fallback selection.
- [x] 1.2 Verify fallback output includes configured defensive exchange, symbol, null rank/score, and full target weight.
- [x] 1.3 Verify sufficient ranked ETF candidates still return Top N selections without selecting the defensive asset.

## 2. Validation

- [x] 2.1 Run the focused momentum scoring tests.
- [x] 2.2 Run `uv run pytest`.
- [x] 2.3 Run OpenSpec validation for the change.
