## 1. Font Loading Baseline

- [x] 1.1 Add non-blocking Inter and Inter Tight font loading links to `apps/web/index.html`.
- [x] 1.2 Update `apps/web/src/styles.css :root` font source comments and `--font-polysans` fallback stack while preserving `--font-inter`.

## 2. Token Source Documentation

- [x] 2.1 Mark `apps/web/src/styles.css :root` as the current implementation token source.
- [x] 2.2 Mark `variables.css` as a design reference that is not imported by the web build.
- [x] 2.3 Add token source documentation covering `styles.css`, `tokens.json`, `variables.css`, and implementation-only spacing additions.

## 3. Validation

- [x] 3.1 Run OpenSpec validation for `establish-font-loading-token-source`.
- [x] 3.2 Run `cd apps/web && npm run test`.
- [x] 3.3 Run `cd apps/web && npm run typecheck`.
- [x] 3.4 Run `cd apps/web && npm run build`.
