## Why

Running `uv run vela-api` repeatedly during local development frequently fails with `ERROR: [Errno 48] Address already in use` on port 8000. Root cause is `apps/api/src/vela_api/cli.py:5` calling `uvicorn.run(..., reload=True)`, which forks a reloader parent + server child; `Ctrl+C` on the parent does not always propagate cleanly and leaves an orphaned worker still bound to 8000. The two services are also launched in separate terminals today (`uv run vela-api` and `npm --prefix apps/web run dev`), which doubles the surface area for stale processes and slows day-to-day iteration. There is currently no developer-facing orchestration that ensures "I have one fresh backend + one fresh frontend running, with predictable output."

## What Changes

- Add a `scripts/dev.sh` orchestration script that cleans stale Vela-owned processes on ports 8000 (FastAPI / uvicorn) and 5173 (Vite), then launches `uv run vela-api` and `npm --prefix apps/web run dev` together in the same terminal with prefixed, interleaved output.
- Implement kill-scoped-by-process-identity: only processes whose command line contains `vela_api` (port 8000) or `vite` (port 5173) are killed, so unrelated services on those ports are never touched.
- Use a two-phase shutdown on exit: `SIGTERM` to both children, wait up to 5 seconds, then `SIGKILL` any survivors; the same grace window is used when killing stale instances at startup.
- Track each child PID in `/tmp/vela-api.pid` and `/tmp/vela-web.pid` so the script can identify its own children for clean shutdown and so stale-PID recovery is possible if a previous run crashed.
- Document the new entry point in `scripts/README.md` (and cross-reference it from the existing per-app READMEs).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. (This change adds a development-experience script and developer documentation; it does not modify any capability-level spec — no backend, API, frontend, or core domain behavior changes.)

## Impact

- New file: `scripts/dev.sh` (executable bash, ~80 lines).
- New documentation: `scripts/README.md` (or appended to existing), plus a short paragraph added to `apps/web/README.md` and `apps/api` docs pointing developers at the script.
- Process model: two background children per invocation, both tracked by PID files in `/tmp`; cleanup runs unconditionally on `EXIT` / `INT` / `TERM`.
- No changes to `vela_api.cli`, no changes to vite config, no changes to dependency manifests, no new Python or npm packages.
- Scope is explicitly local-development only — the script is never invoked by CI, tests, or production paths.
- Out of scope: Windows `.ps1` equivalent (acceptable to defer since the user is on macOS per environment; can be added later if needed).