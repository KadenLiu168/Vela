## 1. Core stitched-curve contract

- [x] 1.1 Add failing pure-domain tests for multiplicative compounding, later-window reset points, three-or-more-window precision, six-place public values, and cumulative total return derived from the unrounded ending factor.
- [x] 1.2 Add failing integrity tests for empty curves, non-positive values, duplicate/non-increasing dates, curve/test-bound mismatches, missing official-session bounds, and typed `unavailable_non_contiguous_windows` results for otherwise valid overlap/gap configurations.
- [x] 1.3 Implement the smallest typed core stitched-OOS helper that distinguishes legitimate non-contiguity from corruption, validates eligible ordered source evidence, performs unrounded Decimal scaling, returns owned/reset-marked points, and raises `PersistedDataContractError` without partial output for corrupt eligible evidence.
- [x] 1.4 Extend the Walk-forward detail query to eager-load OOS equity curves only for detail reads, derive the stitched result from validated parent/child evidence, and prove list reads remain unchanged with temporary-SQLite query/integration tests.

## 2. Typed HTTP detail contract

- [x] 2.1 Add failing schema/router tests that lock both required `stitched_oos` statuses, nullable unavailable values, six-place available Decimal strings, chronological point ownership, reset flags, final compounded values, and the generated OpenAPI shape.
- [x] 2.2 Extend the API response models and Walk-forward detail serializer to expose the core-derived result without browser-side or router-side financial recomputation.
- [x] 2.3 Add API regressions proving current-strategy scoping remains intact, valid non-contiguous windows preserve complete detail with typed unavailability, and corrupt eligible curve/session evidence returns the standard unexpected-error envelope with no partial Walk-forward detail.

## 3. Walk-forward Web presentation

- [x] 3.1 Extend frontend client types/fixtures and add failing component tests for both statuses, API-provided ending net value/cumulative total return, chronological chart points, visible reset disclosure, window ordinal/date boundary content, a programmatic chart label, and non-contiguous unavailability that preserves all other evidence.
- [x] 3.2 Implement the stitched OOS section on Walk-forward Detail by reusing the existing equity-curve presentation primitives or extracting only a narrow shared adapter; do not recalculate financial values or add new cross-window risk metrics in React.
- [x] 3.3 Add deterministic rendered-browser coverage at 1440x1000 and 390x844 for chart readability, reset-boundary access, existing evidence preservation, and absence of page-level horizontal overflow.

## 4. Verification and independent review

- [x] 4.1 Run focused core, query, API, and Web tests after the final implementation revision and repair every target-related failure without writing to `vela.db`.
- [x] 4.2 Run the complete Python gate from the repository root: `uv sync --group dev`, `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, `uv run --no-sync mypy --config-file pyproject.toml`, and `uv run --no-sync pytest`.
- [x] 4.3 Run the complete Web gate from the repository root: `npm --prefix apps/web run lint`, `npm --prefix apps/web run lint:css`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run test`, and `npm --prefix apps/web run build`.
- [x] 4.4 Independently trace every changed requirement through implementation and focused tests, review financial seam/precision semantics plus API/UI accessibility and viewport behavior, repair confirmed defects, and rerun invalidated gates.
- [x] 4.5 Run `openspec validate add-stitched-oos-equity-curve --strict`, `openspec validate --all --strict`, and `openspec doctor`; inspect the final scoped diff and confirm no migration, persisted-data mutation, archive, commit, or push occurred.
