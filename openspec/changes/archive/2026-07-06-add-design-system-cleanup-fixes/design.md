## Context

The web frontend's global stylesheet contains four mechanical
violations of the `design-system` capability (F-204) and one a11y
issue (F-206) inherited from the Initiative's design review on
2026-07-06. Neither is a design decision; both are mechanical
cleanup that closes two open items in the parent Initiative.

The brand has committed to giving every typography-related property
a token (per the archived `add-design-system-spec` change), so the
last four magic `line-height: 1.15;` declarations belong behind a
token. For headings, the page-level titles have always been
semantically `<h2>`; this is a Trunk Test gap that real screen-reader
users would experience as a missing "this page is about..." cue.

## Decisions

1. **One new token, no scale expansion.**
   - Alternative: keep `--leading-tight` and add `--leading-tighter`,
     `--leading-tightest` for fine-grained scale.
   - Rationale: all four `1.15` sites collapse onto one token; a
     single new token is the minimum that satisfies the spec. If a
     future call site needs 1.12 or 1.18, that adds a token in its
     own change.

2. **Page h1 replaces h2, does not stack on it.**
   - Alternative: keep the page `<h2>` AND add a hidden `<h1>`
     (`<h1 class="sr-only">...</h1>`).
   - Rationale: hidden h1s are an a11y anti-pattern (introduce
     inconsistency between sighted and screen-reader users). The
     brand h1 in the AppShell banner landmark is correct as a brand
     identity marker; the page-level h1 is correct as a page title;
     they live in different landmarks and WAI-ARIA explicitly
     permits this.

3. **No heading-level changes elsewhere.**
   - Alternative: also refactor every `<h3>` in `.holdings-section`
     and elsewhere to match the new convention.
   - Rationale: out of scope for this change. The Initiative's
     later phases cover typography refactors.

## Risks / Trade-offs

- **Trunk Test regression risk** if a page already has a hidden
  implicit heading via `<strong>` — mitigation: read each page
  render in DevTools → Accessibility tree before merging.
- **One-line `.tsx` edits are easy to fat-finger** — mitigation:
  diff review catches a stray `<h1>` typo immediately.

## Migration Plan

Single PR. Steps inside:

1. Add `--leading-tight: 1.15;` to `tokens.css`.
2. Replace 4 sites in `styles.css`.
3. Change `<h2>` → `<h1>` in each of 3 pages.
4. Run `openspec validate`, `npm test`, `npm run build`.
5. Archive.
