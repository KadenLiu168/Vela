## ADDED Requirements

### Requirement: Fixed benchmarks retain absolute distribution-risk metrics
Each newly calculated fixed benchmark SHALL retain its own Historical VaR 95%, Historical CVaR 95%, Skewness, Excess Kurtosis, effective observation count, and tail observation count using exactly the same effective-return, threshold, rank, sign, correction, precision, and version semantics as the strategy.

#### Scenario: Identical strategy and benchmark returns produce identical metrics
- **WHEN** the strategy and one fixed benchmark have identical effective return sequences
- **THEN** their distribution metrics and counts are identical
- **AND** remain persisted on their separate curve owners

#### Scenario: Existing relative metrics remain unchanged
- **WHEN** distribution-risk metrics are calculated for fixed benchmarks
- **THEN** return, drawdown, Volatility, Sharpe, Sortino, Calmar, duration, TE/IR, CAPM/capture, cost, curve, and identity semantics remain unchanged
