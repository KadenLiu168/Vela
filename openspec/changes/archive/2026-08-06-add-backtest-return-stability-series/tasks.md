## 1. Preconditions and persisted-curve derivation

- [x] 1.1 Confirm `add-stitched-oos-equity-curve` is complete or archived, rebaseline its final reset/exclusion contract plus the limited shared API schema/client files and Walk-forward regressions, and preserve unrelated work and `vela.db`.
- [x] 1.2 Add failing pure tests proving adjacent persisted net-value return reconstruction, source/effective counts, unquantized Decimal reconstruction/compounding/mean/variance intermediates, and rejection of duplicate/non-increasing dates and non-positive values.
- [x] 1.3 Add failing independent-oracle tests for the first and subsequent 63-effective-session Rolling Return, population Volatility, risk-free Sharpe using the existing float square-root annualization convention, six-place output, and exact window start/end dates.
- [x] 1.4 Add failing rolling boundary tests for fewer than 64 points, zero dispersion, empty curves, missing/malformed legacy risk-free-rate evidence, and deterministic repeated derivation.
- [x] 1.5 Add failing calendar tests for cross-month/year return assignment, compounding, observation counts, empty-bucket omission, requested-scope boundary flags, and the case where requested bounds cover a natural period while curve endpoints fall inside it because calendar boundaries are not official sessions; prove the flag is not derived from endpoint dates.
- [x] 1.6 Implement the smallest immutable public return-stability result types/function and exports without persistence, current-market/calendar reads, filling, or expanding windows.

## 2. Backtest Detail query and typed HTTP contract

- [x] 2.1 Add focused query tests proving detail reads derive strategy and ordered benchmark stability from already owned curves while list reads do not load or derive the series.
- [x] 2.2 Integrate pure derivation into the detail query/service boundary, parse historical risk-free evidence explicitly, and fail closed on malformed curves without mutating persisted rows.
- [x] 2.3 Add failing response-schema and OpenAPI tests for required stability metadata, statuses, dates, counts, nullable Sharpe, requested-scope partial flags, six-place strings, strategy result, and ordered benchmark results.
- [x] 2.4 Extend Backtest Detail serialization to expose the core result without router-side arithmetic while keeping run-creation and list payloads unchanged.
- [x] 2.5 Add API regressions for empty/short curves, legacy no-benchmark/no-risk-free histories, strategy scoping, corrupt curve error envelopes, and exact API-to-core equality.

## 3. Backtest Detail presentation

- [x] 3.1 Extend frontend client types and deterministic fixtures for all rolling/calendar statuses, strategy/benchmark series, requested-scope partial periods, and legacy empty states.
- [x] 3.2 Add failing component tests for the 63-session label, rolling metric selector, strategy/benchmark identity, API value fidelity, accessible exact-value fallback, and absence of browser-side recomputation.
- [x] 3.3 Implement one selectable rolling comparison visualization using existing presentation primitives or the smallest narrow shared adapter, without mixing differently scaled metrics on one axis.
- [x] 3.4 Add failing component tests for monthly/yearly and entity selection, counts, requested-period partial markers without data-completeness claims, empty states, and preservation of existing Backtest Detail tabs/actions.
- [x] 3.5 Implement accessible monthly/yearly table/heatmap presentation without nested card grids or fabricated empty periods.
- [x] 3.6 Add a Walk-forward parent regression proving available/unavailable stitched OOS states never render rolling/calendar metrics and existing OOS detail links remain navigable.
- [x] 3.7 Add deterministic rendered-browser coverage at 1440x1000 and 390x844 for selectors, charts, exact-value access, partial markers, existing navigation, and absence of page-level horizontal overflow.

## 4. Verification and independent review

- [x] 4.1 Run all focused core, query, API, component, and rendered-browser tests after the final revision and repair every related failure without writing to `vela.db`.
- [x] 4.2 Run the complete Python gate: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 4.3 Run the complete Web gate: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`.
- [x] 4.4 Independently trace every requirement through implementation and focused tests; review persisted-precision and mixed Decimal/float square-root semantics, window indexing, risk-free legacy handling, requested-scope calendar flags without official-session completeness claims, API payload size, stitched exclusion, accessibility, and viewports and repair confirmed defects.
- [x] 4.5 Run `openspec validate add-backtest-return-stability-series --strict`, `openspec validate --all --strict`, and `openspec doctor`; inspect the scoped diff and confirm no migration, persisted-data mutation, archive, commit, or push occurred.
