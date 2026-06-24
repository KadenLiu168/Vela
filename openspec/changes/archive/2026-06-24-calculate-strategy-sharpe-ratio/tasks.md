## 1. Strategy Configuration

- [x] 1.1 Add `performance.risk_free_rate` to the checked-in `config/strategy_v1.yaml`.
- [x] 1.2 Add a frozen Pydantic performance configuration model with non-negative `risk_free_rate`.
- [x] 1.3 Update strategy configuration tests for loading, required groups, and invalid negative risk-free rate.

## 2. Sharpe Ratio Calculation

- [x] 2.1 Add a frozen Sharpe ratio result dataclass with nullable `sharpe_ratio`.
- [x] 2.2 Implement Sharpe ratio as `(annualized_return - risk_free_rate) / volatility`, quantized to six decimal places.
- [x] 2.3 Return no Sharpe ratio when annualized return is unavailable, volatility is unavailable, or volatility is zero.
- [x] 2.4 Export the Sharpe ratio result type and calculator from `vela_core`.

## 3. Verification

- [x] 3.1 Add unit tests for typical positive Sharpe ratio and negative excess return.
- [x] 3.2 Add unit tests for unavailable annualized return, unavailable volatility, and zero volatility.
- [x] 3.3 Run targeted tests, full tests, lint, type check, and OpenSpec validation.
