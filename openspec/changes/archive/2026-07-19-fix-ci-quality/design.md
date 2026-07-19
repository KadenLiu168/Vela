## Context

GitHub CI "Python quality" job fails with `exit code 1`, blocking merges. Root cause (confirmed by running the committed `e89bc34` in an isolated git worktree): the test `apps/cli/tests/test_sync_etf_pool.py::test_sync_etf_pool_uses_default_inputs` asserts its captured `strategy_config_path` equals the hardcoded absolute path `Path("/Users/kaden/Vela/config/strategy_v1.yaml")`. The CLI resolves its default config path at runtime as `DEFAULT_STRATEGY_CONFIG_PATH = ROOT / "config" / "strategy_v1.yaml"` (`apps/cli/src/vela_cli/main.py:45`), which is correct on every machine — it just does not equal the hardcoded string unless the repo lives at exactly `/Users/kaden/Vela`. Hence the test passes locally and fails on GitHub runners (path `/home/runner/work/...`).

Two additional CI messages are non-fatal noise from outdated GitHub Actions: the `Node.js 20 is deprecated` warning (the three actions still bundle the Node 20 runtime, which GitHub runners now force to Node 24) and `Cache service responded with 400` (the old `actions/cache` backend used by `setup-uv@v3`/`setup-node@v4`). Neither causes the exit 1.

## Goals / Non-Goals

**Goals:**
- Make the failing test pass on every environment (local, CI, any checkout path) by asserting against the CLI's real default path constant.
- Remove the two non-fatal CI warnings by upgrading the actions to Node 24 runtimes: `checkout` and `setup-node` to v5, and `setup-uv` to v7 (v5/v6 still bundle Node 20 and would not clear the warning).
- Ship both in a single change so CI goes green + quiet in one PR.

**Non-Goals:**
- Changing any production behavior, API, DB schema, or dependency.
- Fixing the three other open changes (`fix-bootstrap-stale-config`, `add-signal-provenance`, `fix-signal-latest-strategy-scoping`) — they are out of scope and remain uncommitted in the working tree.
- Adding new test coverage beyond the one-line assertion correction.

## Decisions

- **Assert against `cli.DEFAULT_STRATEGY_CONFIG_PATH`, not a repo-relative recomputation.** The test already does `from vela_cli import main as cli`, so referencing `cli.DEFAULT_STRATEGY_CONFIG_PATH` reuses the exact constant the production CLI uses. This guarantees the test and the CLI can never drift apart (alternative: recompute `REPO_ROOT / "config" / "strategy_v1.yaml"` — rejected because it duplicates the resolution logic and could diverge from the CLI).
- **Bundle the CI action upgrade with the test fix in one change.** The action upgrade alone does NOT fix exit 1 (the test still fails); the test fix alone makes CI green but leaves the warnings. Combining them delivers a fully clean CI in a single, coherent PR rather than two separate ones.
- **Upgrade `checkout` & `setup-node` to v5; `setup-uv` to v7 (not v5/v6).** `checkout@v5` and `setup-node@v5` are well-tested Node 24 drop-ins that eliminate the Node 20 deprecation warning with no relevant breaking changes. (`checkout@v6` exists but adds credential-file changes; `setup-node@v6` exists but changes auto-caching defaults — neither brings benefit here.) `setup-uv@v7` is the first published major tag that uses Node 24; `setup-uv@v5` and `@v6` still bundle Node 20, so bumping it to v5 would leave the deprecation warning in place. Its current cache dependency replaces the legacy backend used by v3. The only `setup-uv` input this workflow uses (`enable-cache: true`) is stable across v3→v7, so behavior is unchanged.
- **Keep `enable-cache: true` and `cache: npm` as-is.** `setup-uv@v7` enables caching by default and the workflow already sets `enable-cache: true` explicitly (→ no change); `setup-node@v5` changes cache auto-detection but the explicit `cache: npm` input is unaffected.

## Risks / Trade-offs

- **[Risk] Upgrading actions could surface a runner/compatibility quirk.** → Mitigation: `checkout@v5`, `setup-node@v5`, and `setup-uv@v7` use Node 24; GitHub-hosted `ubuntu-latest` meets the required runner version; the change is config-only and revertable.
- **[Risk] The test fix masks a real path-resolution bug elsewhere.** → Mitigation: verified the CLI resolves the correct path on both `/Users/kaden/Vela` and `/private/tmp/...`; only the assertion was wrong, not the resolution logic.
- **[Trade-off] One change mixes a code fix with a config fix.** → Accepted: both serve the single goal "make CI green and quiet," and each edit is independently reviewable within the change.

## Migration Plan

1. Edit `apps/cli/tests/test_sync_etf_pool.py` line 61: replace `Path("/Users/kaden/Vela/config/strategy_v1.yaml")` with `cli.DEFAULT_STRATEGY_CONFIG_PATH`.
2. Edit `.github/workflows/ci.yml`: `actions/checkout@v4` → `@v5` (both the Python job and the Frontend job), `astral-sh/setup-uv@v3` → `@v7` (Python job), `actions/setup-node@v4` → `@v5` (Frontend job).
3. Run `uv run pytest` locally to confirm `test_sync_etf_pool_uses_default_inputs` passes (and the full suite stays green).
4. Commit and push; CI should report Python quality green with no deprecation/cache warnings.
5. Rollback: revert the two files (both are self-contained, low-risk).

## Open Questions

- None.
