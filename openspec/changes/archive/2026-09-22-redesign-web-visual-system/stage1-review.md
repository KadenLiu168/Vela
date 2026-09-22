# Stage 1 readiness review

Date: 2026-09-21. Profile: high-risk (public UI and shared visual contracts).
Reviewed repository HEAD: `e20d8e37a91d56ab2b0053b8f16aaa1ecbbca97a`.
Initial worktree: only this untracked Change directory; implementation tasks 0/34.
Conclusion: 修改后适合实施. This is planning acceptance, not implementation acceptance.

## Findings and artifact repairs

| Classification | Finding and current evidence | Minimal repair |
| --- | --- | --- |
| Pre-implementation fix | `tests/test_inter_font.py` opens Inter assets, asserts its axes/features and invokes the subset script. Deleting `scripts/fonts/inter/` leaves five Python tests invalid; `scripts/README.md` still documents that script. | Explicit Geist test migration using existing FontTools, font documentation update, and complete Python gate in addition to Web gate. No Python business change or dependency cleanup. |
| Pre-implementation fix | `research-workbench-ui` requires Bootstrap to remain acid-lime in its next-action scenario; four original deltas leave that contract behind. | Add the fifth delta replacing visual vocabulary only; preserve all action priority, focus, date, and accessibility rules. |
| Pre-implementation fix | Living `card-type-scale` requires `dt` and `dd` to share a leading token; the new meta/dense roles are 16px and 20px. Current `.compact-list dt/dd` both use `--leading-body-card`. | Specify shared 20px leading as the compact-list exception and verify actual Sans/Mono baselines; keep standalone meta 11/16. Preserve existing tracking values. |
| Pre-implementation fix | New status requirement classified empty as status, while design chose neutral borders; text-only token wording excluded required market figures/chart labels. | State neutral empty treatment and contrast-qualified status/market/chart text exceptions. Permit existing local state bindings to select canonical tokens. |
| Pre-implementation fix | `DescriptionItem`, `TableCells`, and Command Palette contain mixed names, identifiers and formatted values; restricting semantic classes to tables cannot implement all typography requirements. | Permit narrow classes/spans on existing presentation paths, with accessible names, order, data and interaction unchanged; forbid content guessing and indiscriminate Mono inheritance. |
| Pre-implementation fix | `lint:css` invokes Stylelint only; the root guard is a separate `lint:css:root` script. Literal zero-match searches would also reject the negative tests required by task 1.2. | Explicit root-guard validation plus a canonical-path static assertion; runtime-only absence checks retain non-bundled negative fixtures. |
| Pre-implementation fix | Token-doc scenario required `git ls-files` during generation, conflicting with separate delivery authorization. | Require current/unignored output during Apply and tracked output after authorized delivery. |
| Pre-implementation fix | Responsive acceptance lacked concrete route/state/fixture evidence; real Dashboard actions can write persistent data. | Specify representative routes/states and boundary widths, use intercepted API fixtures/stories, record browser evidence, and forbid real data-mutating actions in visual verification. |
| Recorded tradeoff | `public/favicon.svg` is a standalone existing lime graphic outside `src/`. | Explicitly retain the existing icon artwork; the Change migrates source tokens and font assets, not icon design. |
| Recorded tradeoff | Official v1.7.2 release page is reachable, but the attempted GitHub tree API request returned HTTP 403. This review did not independently verify the two font binaries/hashes. | Preserve pinned hashes as acceptance criteria; downloading and verifying binaries is an early Apply prerequisite before Inter removal. Do not claim binary verification based on the release page. |

## Requirement → design → task → code → planned validation

Paths below are relative to the repository root. Design decisions refer to `design.md`.

| Requirement group | Design decision | Tasks | Existing code constraint | Planned test / evidence |
| --- | --- | --- | --- | --- |
| Canonical file/catalog, semantic colors, legacy absence | 1, 4 | 1.2, 3.1, 3.4, 8.1–8.2 | `apps/web/src/styles/tokens.css`, global CSS, inline TSX strings | Exact token/alias checks, canonical-root rejection, runtime scan and invalid fixtures |
| Sans/Mono roles, canonical mono name, removal of display/Inter aliases | 2–4 | 2.1–2.4, 3.2, 4.4 | Global font inheritance, `DescriptionItem.tsx`, `tablePrimitives.tsx`, Command Palette mixed content | Role assertions plus browser computed fonts and mixed-language values |
| Pinned OFL fonts, preload linkage, real variable families, feature retirement | 2 | 2.1–2.4 | `tests/test_inter_font.py`, `index.html`, `scripts/fonts/inter/`, `scripts/README.md` | Binary hashes/axes/cmap/license, preload/font-face tests, production asset load and fallback review |
| Research scale, line-height tokens, page heading/brand hierarchy | 3 | 3.3, 4.1, 4.4 | `styles.css` heading/brand/card rules and shared tokens | Exact size/leading tests; non-heading brand and route h1 behavior; responsive screenshots |
| Four card rungs, role mapping, tracking, shared compact lists and baselines | 3–4 | 3.3, 4.4, 9.2 | `.compact-list dt/dd`, `.panel-primary`, `.metric-card`, description callers | Shared 20px row leading, standalone 11/16, numeric tabular styling, actual baseline/overflow review |
| Card aliases, surfaces, borders and restrained elevation | 1, 4 | 3.4, 4.3 | `--card-*`, radius/padding aliases, panels/dialog rules | Alias resolution, unchanged spacing/radius, representative card/dialog render |
| Primary/secondary/tertiary, pressed state, Celestial identity | 4–5 | 4.1–4.2, 9.3 | Existing variant classes, `aria-pressed`, AppShell nav | Variant/pressed tests, single primary CTA, keyboard focus and contrast |
| Status versus market direction, neutral empty states | 5 | 5.1–5.2 | `FeedbackMessage.tsx`, local `--status-accent`, `.stability-return-*` | Status-role and signed-return checks; loading/error/empty/success fixtures |
| Dashboard neutral category marker | 5 | 5.3 | `DashboardPage.tsx` inline `barColor` function | Existing Dashboard/data tests, neutral CSS hairline, no new palette |
| Stable chart mapping, series values, direct-label contrast | 6–7 | 1.3, 6.1–6.2 | `seriesColor.ts/.test.ts`, `EquityCurvePlot.tsx`, `ReturnStabilitySection.tsx` | Supported/unknown-key tests, contrast tests, existing geometry/component regressions |
| Single-series ETF and stitched OOS identity | 6 | 6.3 | ETF chart CSS and `StitchedOosSection.tsx` inline stroke | ETF/stitched tests, unchanged geometry, visible label containment |
| Low-contrast metadata and Command Palette semantics | 7 | 7.1–7.2, 9.3 | Palette active/hover selectors and `CommandPalette.test.tsx` | Active metadata pair ≥4.5:1, focus trap/filter/selection/ARIA regressions |
| AppShell/routes, no data or geometry changes | 7, 9 | 4.1, 9.1–9.3, 10.5 | `AppShell.tsx`, App route/navigation tests, chart utility tests | Skip-link/main focus/current nav, route and data regressions; final scoped diff |
| Research-workbench action hierarchy and existing decisions | 9 | 4.2, 5.1, 9.1, 10.1 | `ResearchStatusSection.tsx/.test.tsx`, `researchWorkbench.test.ts` | Preserve action selection/focus tests; Bootstrap sole primary and responsive Dashboard |
| Responsive/motion/accessibility and heading rhythm | 3, 7, 9 | 4.5, 9.1–9.3 | Existing 1024/900/720 CSS, reduced-motion rules, heading spacing | Boundary-width shell checks, representative route/state screenshots, keyboard/motion review, no page overflow |
| Lifecycle, generated tracked docs, static enforcement and stories | 8–9 | 8.1–8.4, 10.1–10.5 | `.gitignore`, token generator, separate root guard, Ladle stories | Generated aliases/catalog, unignored file, invalid guard fixtures, production bundle inspection; tracking only at delivery |

## Validation and Apply constraints

- `openspec validate redesign-web-visual-system --strict`: passes after artifact repairs.
- `openspec validate --all --strict`: 48 passed / 11 failed both before and after repairs. Existing failures concern placeholder Purpose sections, not this Change.
- `openspec doctor`: OpenSpec root ok, no declared reference problems.
- No `openspec verify` command exists in installed CLI help.
- `git diff --check`: passed. Direct whitespace/conflict-marker checks passed for all 10 Change files, including untracked artifacts; every MODIFIED/REMOVED requirement name matches its living spec.
- This stage edits only Change artifacts; no application code, tests, tools, living specs, fonts or persistent data were changed. No implementation suite is required for this documentation-only review.
- Apply must complete both project gates after final relevant edits and retain real-browser acceptance evidence. Do not replace visual/font evidence with static checks alone.
- Downloaded font hashes/metadata and actual rendered contrast/layout remain implementation acceptance work. Do not remove Inter until replacement verification passes.
- Keep the Change active for implementation and later review. Archive, commit and push are not authorized by stage 1.

Repair inventory: `proposal.md`, `design.md`, `tasks.md`, `specs/design-system/spec.md`, `specs/card-type-scale/spec.md`, new `specs/research-workbench-ui/spec.md`, and this review. Existing `web-frontend-app` and `command-palette` deltas remain unchanged.
