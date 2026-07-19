## 1. Fix the hardcoded absolute path in the CLI test

- [x] 1.1 In `apps/cli/tests/test_sync_etf_pool.py`, replace the hardcoded `Path("/Users/kaden/Vela/config/strategy_v1.yaml")` in `test_sync_etf_pool_uses_default_inputs` (line 61) with `cli.DEFAULT_STRATEGY_CONFIG_PATH` (the test already imports `from vela_cli import main as cli`).
- [x] 1.2 Run `uv run --no-sync pytest apps/cli/tests/test_sync_etf_pool.py` and confirm `test_sync_etf_pool_uses_default_inputs` passes on the current checkout.
- [x] 1.3 Run the full `uv run --no-sync pytest` suite and confirm no regressions (the rest of the suite stays green).

## 2. Upgrade GitHub Actions to Node 24 runtimes to clear CI warnings

- [x] 2.1 In `.github/workflows/ci.yml`, bump `actions/checkout@v4` → `actions/checkout@v5` (Python job and Frontend job).
- [x] 2.2 Bump `astral-sh/setup-uv@v3` → `astral-sh/setup-uv@v7` (Python job; `enable-cache: true` already set, behavior unchanged; v7 is the first published major tag using the Node 24 runtime, while v5/v6 still bundle Node 20).
- [x] 2.3 Bump `actions/setup-node@v4` → `actions/setup-node@v5` (Frontend job; explicit `cache: npm` already set, behavior unchanged).

## 3. Validate locally and confirm CI-clean intent

- [x] 3.1 Run `uv run --no-sync ruff check .`, `uv run --no-sync ruff format --check .`, and `uv run --no-sync mypy --config-file pyproject.toml` to confirm no new lint/type issues from the change.
- [x] 3.2 Confirm the implementation diff (excluding this change's OpenSpec artifacts) is limited to `apps/cli/tests/test_sync_etf_pool.py` and `.github/workflows/ci.yml` (no production code touched).
- [ ] 3.3 After the change is pushed, confirm the GitHub Actions run passes both quality jobs and contains neither the Node.js 20 deprecation warning nor `Cache service responded with 400`.
