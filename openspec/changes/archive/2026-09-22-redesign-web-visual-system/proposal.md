## Why

Vela Web currently couples product identity, interaction, system feedback, market direction, and chart identity to a Linear-style midnight and acid-lime palette while all semantic font roles resolve to Inter Variable. This makes visually similar colors carry incompatible meanings and prevents data typography from having a real monospace identity, so the frontend needs one coordinated contract migration to a restrained quantitative-research visual system.

## What Changes

- **BREAKING** Replace the legacy color-name token vocabulary (`--color-*`, legacy `--surface-*`, and `--color-series-*`) with semantic surface, border, text, interaction, status, China-market, and chart roles. Migrate every Web consumer in the same change and leave no legacy visual-token consumer or compatibility alias after completion.
- **BREAKING** Replace `--font-inter-variable`, `--font-display`, and `--font-berkeley-mono` with `--font-sans` and `--font-mono`, backed by separately loaded Geist Sans Variable and Geist Mono Variable WOFF2 resources from a pinned official OFL release.
- Replace the oversized display ladder with a research-workstation type scale, keep every `line-height` routed through a `--leading-*` token, and apply Sans to language/UI roles while applying Mono plus tabular numerals only to quantitative and code-like roles.
- Rebuild canvas, panel, raised, hover, border, and text hierarchy around the Celestial Research blue-black system without adding a light theme, new spacing/radius systems, or shadow-led elevation.
- Keep exactly the existing primary/secondary/tertiary button variants, but move primary interaction and focus identity to Celestial Blue and preserve the one-prominent-primary-CTA-per-view hierarchy.
- Separate system feedback (`success`, `warning`, `danger`, `info`) from China-market movement (`market-up`, `market-down`, `market-flat`) and prevent either vocabulary from substituting for the other.
- Replace the categorical chart palette while preserving stable key-based mapping for strategy, equal-weight monthly, CSI 300 buy-and-hold, and deterministic future-key fallbacks; single-series ETF and stitched OOS curves use chart identity rather than interaction identity.
- Restyle AppShell, cards, tables, feedback surfaces, charts, and Command Palette through semantic tokens while preserving accessibility behavior, route behavior, data logic, and chart geometry. Keep JSX structure except narrow semantic classes/presentational spans needed to distinguish language from data.
- Neutralize the Dashboard ETF category hairline because it currently communicates unlabeled category identity by color alone; do not introduce another component-specific palette.
- Update design-system lint/static contracts, vendored-font provenance and license material, font preloads, generated token documentation, affected stories/tests, and responsive visual checks.
- Correct the OpenSpec lifecycle wording so a validated active Change authorizes implementation and archive remains a post-implementation step rather than a prerequisite for editing `tokens.css`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `design-system`: Replace the Linear palette, Inter-only typography, old scale, acid-lime interaction rules, coupled feedback colors, and old chart tokens with the Celestial Research semantic contracts and dual-font runtime.
- `card-type-scale`: Replace legacy display/mono token names and exact Inter requirements while retaining role-based card typography and tabular quantitative alignment.
- `web-frontend-app`: Replace the acid-lime navigation contract and preserve application accessibility, chart identity, responsive behavior, and one-primary-CTA hierarchy under the new semantic system.
- `command-palette`: Replace the historical legacy-token constraint with semantic surface/text/status/font roles while keeping the existing keyboard, focus, ARIA, filtering, and selection behavior unchanged.
- `research-workbench-ui`: Replace the remaining acid-lime primary-CTA wording with the shared semantic primary treatment, preserving every next-action selection rule.

## Impact

- Runtime design source: `apps/web/src/styles/tokens.css`, `apps/web/src/styles.css`, and `apps/web/index.html`.
- Font assets and provenance: `apps/web/public/fonts/`, `scripts/fonts/`, and the font section of `scripts/README.md`; Inter resources are removed after Geist Sans/Mono replacements and their OFL notice are verified. Migrate `tests/test_inter_font.py` into Geist font-contract coverage using the existing FontTools dependency.
- Narrow React/TypeScript consumers: stable chart token mapping, inline legacy color references, Dashboard category marker, and any semantic class needed to distinguish numeric from language cells. Backend APIs, routing, data transformations, and chart geometry algorithms remain unchanged.
- Contract tests and presentation coverage: series mapping, static CSS/token/font contracts, AppShell and Command Palette behavior, chart consumers, stories, and responsive review at the existing 1024px, 900px, and 720px breakpoints.
- Tooling/documentation: `apps/web/.stylelintrc.json`, `scripts/build-tokens-reference.mjs` only if required for the new groups, a narrow `.gitignore` exception for generated `docs/tokens.md`, and the regenerated tracked token reference.
- No new npm dependency or UI framework is introduced. The complete Web and Python CI-equivalent gates are required because the migration replaces Python font tests and removes the Python Inter subset script. Backend business logic and persistent data remain outside scope.
