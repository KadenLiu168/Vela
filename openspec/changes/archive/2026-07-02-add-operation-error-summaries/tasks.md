## 1. Tests

- [x] 1.1 Add Dashboard tests for market data fetch, signal generation, and backtest run API error responses that assert operation name, reason, and next-step guidance.
- [x] 1.2 Add coverage that a technical API error detail is not the only visible failure guidance.

## 2. Implementation

- [x] 2.1 Store operation request failures with `ApiClientError` reason, status, and kind instead of only the normalized kind.
- [x] 2.2 Render structured operation error summaries with operation-specific reason and next-step guidance.
- [x] 2.3 Keep successful operation summaries and existing loading behavior unchanged.

## 3. Validation

- [x] 3.1 Run focused frontend tests for Dashboard operation errors.
- [x] 3.2 Run frontend lint, typecheck, build, and OpenSpec validation.
