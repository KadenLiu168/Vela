## Why

Signal Detail target holdings already has the broader COP-133 editorial table treatment, but the table still needs a narrower typography and alignment pass so numeric columns scan like a printed data report without changing table structure.

## What Changes

- Fine-tune `.holdings-table` header typography, row rhythm, and Mist hairline separation for the Signal Detail target holdings table.
- Make target weight, rank, and score columns consistently right-aligned with tabular numerals.
- Keep exchange, symbol, and fallback text columns left-aligned and readable.
- Preserve the existing table DOM, text, test selectors, API usage, route behavior, and `holdings-table-wrap` horizontal scrolling.
- Follow the Explore auto decision to keep the implementation CSS-only and avoid new table abstractions.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `web-frontend-app`: Add specific Signal Detail holdings table typography, numeric alignment, hairline divider, and narrow-screen scroll requirements.

## Impact

- Affected code: `apps/web/src/styles.css`
- Affected tests: existing `apps/web/src/App.test.tsx` coverage for Signal Detail target holdings behavior
- Affected specs: `openspec/specs/web-frontend-app/spec.md`
- No API, route, data model, dependency, JSX structure, sorting, filtering, pagination, or shared table component changes.
