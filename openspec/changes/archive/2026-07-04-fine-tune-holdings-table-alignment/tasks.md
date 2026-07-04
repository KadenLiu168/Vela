## 1. Signal Detail Holdings Table Refinement

- [x] 1.1 Refine `.signal-detail-page .holdings-table` header typography, row padding, line height, and Mist divider treatment using existing design tokens.
- [x] 1.2 Ensure target weight, rank, and score columns and headers use tabular numerals with right alignment while text columns remain left-aligned.
- [x] 1.3 Confirm `holdings-table-wrap` horizontal scrolling, table DOM, rendered text, API usage, and test selectors remain unchanged.

## 2. Validation

- [x] 2.1 Run OpenSpec validation for `fine-tune-holdings-table-alignment`.
- [x] 2.2 Run `cd apps/web && npm run test`.
- [x] 2.3 Run `cd apps/web && npm run typecheck`.
- [x] 2.4 Run `cd apps/web && npm run build`.
- [x] 2.5 Complete review/fix/validate loop and record final findings before archive.
