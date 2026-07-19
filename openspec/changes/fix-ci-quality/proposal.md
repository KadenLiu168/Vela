## Why

GitHub CI "Python quality" job fails with `exit code 1`, blocking all merges. The failure is a single test (`apps/cli/tests/test_sync_etf_pool.py::test_sync_etf_pool_uses_default_inputs`) that hardcodes the developer's absolute machine path `/Users/kaden/Vela/config/strategy_v1.yaml` in its assertion. That path only matches when the repo is checked out at exactly `/Users/kaden/Vela`, so the test passes locally but fails on GitHub runners (and any other machine). Two accompanying warnings — Node.js 20 deprecation and `Cache service responded with 400` — are non-fatal noise from outdated GitHub Actions. Fixing all three in one change makes CI fully green and quiet.

## What Changes

- Fix the test assertion in `apps/cli/tests/test_sync_etf_pool.py` to compare against `cli.DEFAULT_STRATEGY_CONFIG_PATH` (the CLI's real default config path, defined in `apps/cli/src/vela_cli/main.py:45`) instead of the hardcoded `/Users/kaden/Vela/config/strategy_v1.yaml`. This is the change that actually makes CI pass.
- Upgrade the GitHub Actions in `.github/workflows/ci.yml` to versions that ship the Node 24 runtime (GitHub-hosted runners now deprecate the Node 20 runtime that the old actions bundle): `actions/checkout@v4` → `@v5` and `actions/setup-node@v4` → `@v5` (both are Node 24 drop-ins), and `astral-sh/setup-uv@v3` → `@v7`. `setup-uv@v7` is the first published major tag that uses Node 24; v5/v6 still bundle Node 20, so bumping it to v5 would NOT clear the deprecation warning. Its cache implementation uses a current `@actions/cache` dependency, avoiding the legacy cache backend behind the reported 400. No behavior change: `setup-uv@v7` still accepts the existing `enable-cache: true`, and `setup-node`'s explicit `cache: npm` is unaffected by its auto-detection change.

## Capabilities

### New Capabilities

(None — this change does not introduce product capabilities.)

### Modified Capabilities

- `test-suite-validation`: ADD a requirement formalizing that tests must not hardcode machine-specific absolute paths. This *specializes* the existing `Tests assert contracts over configuration snapshots` portability requirement (which targets config-value literals such as ETF pool counts and `strategy_id`) to the filesystem-path axis: the failing test encoded the developer's absolute path `/Users/kaden/Vela/config/strategy_v1.yaml` in its assertion, which only matches when the repo is checked out at that exact location; this breaks the suite on CI and any other machine. Codifying path portability prevents recurrence.

## Impact

- `apps/cli/tests/test_sync_etf_pool.py`: one-line assertion change (test-only).
- `.github/workflows/ci.yml`: action version bumps — `actions/checkout@v4` → `@v5` (Python and Frontend jobs), `actions/setup-node@v4` → `@v5` (Frontend job), `astral-sh/setup-uv@v3` → `@v7` (Python job).
- No production code, API, or dependency changes. No user-facing impact.
