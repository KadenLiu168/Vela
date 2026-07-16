## 1. ESLint Baseline

- [x] 1.1 Reproduce and document the current `npm --prefix apps/web run lint` failures
- [x] 1.2 Refactor affected route page loading-state effects so ESLint passes without disabling rules
- [x] 1.3 Verify the affected route page tests still pass

## 2. CSS Lint Baseline

- [x] 2.1 Reproduce and document the current `npm --prefix apps/web run lint:css` failures
- [x] 2.2 Replace flagged literal CSS values with existing design tokens
- [x] 2.3 Verify CSS lint passes without weakening Stylelint rules

## 3. Validation and Archive

- [x] 3.1 Run frontend lint, CSS lint, tests, typecheck, and build
- [x] 3.2 Run OpenSpec validation for `fix-web-lint-baseline` and full OpenSpec validation
- [ ] 3.3 Archive `fix-web-lint-baseline`
