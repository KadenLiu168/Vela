## Context

Local development of Vela today means running two commands in two terminals:

- `uv run vela-api` — starts uvicorn (FastAPI) on port 8000 via `apps/api/src/vela_api/cli.py:5` (`reload=True`).
- `npm --prefix apps/web run dev` — starts Vite on port 5173; `apps/web/vite.config.ts` proxies `/api/*` to 8000.

`reload=True` is convenient for hot reload, but uvicorn spawns a reloader parent + server child. `Ctrl+C` on the parent occasionally leaves the child alive holding 8000, so the next `uv run vela-api` aborts with `[Errno 48] Address already in use`. The user has no automated way to recover except to find the orphan PID manually.

There is also no single-command story for "spin up the whole local stack". The two processes must be launched and torn down independently, which doubles the surface area for stale processes.

This change introduces one orchestration script (`scripts/dev.sh`) that wraps both launches, cleans stale Vela-owned processes by port + command-line identity before starting, and tears both children down cleanly on `Ctrl+C`.

## Goals / Non-Goals

**Goals:**

- Make `uv run vela-api` idempotent: running it via the orchestrator never produces "Address already in use" for Vela's own processes.
- Run backend and frontend together from one terminal with prefixed, interleaved output so the user can read both streams in order.
- Cleanly stop both children on `Ctrl+C` (SIGTERM → 5s grace → SIGKILL), including the orphaned-reloader-child case.
- Never kill processes that aren't ours: an unrelated service on port 8000 or 5173 is left alone.
- Stay out of `vela_api.cli`, vite config, and any business-logic file — this is a development-experience shell script only.

**Non-Goals:**

- No Windows support in this change. macOS/Linux only (the environment is macOS per session metadata). A `.ps1` equivalent may be added later.
- No process supervisor (systemd, supervisord, foreman) — bash + `trap` is sufficient for one terminal session.
- No colored output, log rotation, or remote-tail features.
- No changes to `reload=True` (kept as-is; the script handles the cleanup that reload's parent/child model makes necessary).
- No CI integration, no production deployment path, no effect on `pyproject.toml` or `package.json`.

## Decisions

- **Bash script in `scripts/dev.sh`, not a Python CLI.**
  - Rationale: it is purely a developer-experience wrapper with no domain logic; bash keeps it transparent and easy to tweak without a new entry point. No new package, no new dependency, no `pyproject.toml` change.
  - Alternative considered: a Python `vela-api-dev` click/typer CLI. Rejected because it would add a new package and an extra import path for behavior that is shell-shaped.

- **Kill by port + command-line regex, not PID file alone.**
  - Rationale: PID files can be stale (previous run crashed, file left behind). Combining `lsof -ti:<port>` with `ps -p <pid> -o command=` and a regex match (`vela-api|vela_api` for 8000, `vite` for 5173) catches both the PID-file-known case and the orphan case. The regex's alternation covers two real invocation forms: the `vela-api` console-script (`uv run vela-api`, what the user typed) and direct uvicorn (`uv run uvicorn vela_api.main:app`). The reloader worker child spawned via `multiprocessing.spawn` does NOT carry either substring on its command line, so it is reached transitively by signalling the reloader parent — uvicorn propagates SIGTERM to the worker on shutdown.
  - Alternative considered: only trust the PID file. Rejected because it cannot clean orphans left from a crashed previous session.

- **Only kill processes whose command line matches `vela-api|vela_api` or `vite`.**
  - Rationale: if another developer tool happens to bind 8000 or 5173 (e.g. a debug proxy, an alternative web server), the orchestrator must not touch it. Matching on command line is the cheap, safe scope.
  - Alternative considered: kill anything on the port. Rejected — too aggressive.

- **5-second SIGTERM grace, then SIGKILL.**
  - Rationale: uvicorn's own shutdown on `Ctrl+C` takes well under 5s; vite shutdown is similarly fast. 5s is the standard local-dev grace and is short enough that a wedged process does not block the developer.
  - Alternative considered: 3s (faster turnaround) or 10s (more forgiving for slow requests). 5s balances both.

- **PID files in `/tmp` (`/tmp/vela-api.pid`, `/tmp/vela-web.pid`).**
  - Rationale: `/tmp` is the standard location for ephemeral runtime state on macOS/Linux, is auto-cleared on reboot, and never touches the repo (no `.gitignore` entry needed). Multi-user safety is acceptable because the file names include the service name; collisions are unlikely and would manifest as a misidentified stale process, not data loss.
  - Alternative considered: `XDG_STATE_HOME` (Linux-spec-correct but unconfigured on macOS by default) or `.run/` inside the repo (would need gitignore + accidental-commit risk). Both rejected as net-worse.

- **Trap-based cleanup on `EXIT INT TERM`.**
  - Rationale: `trap '... ' EXIT INT TERM` runs the cleanup regardless of which signal terminates the parent shell, including the natural-exit case (no signal at all). One trap, one cleanup function, applied to both children.
  - Alternative considered: only trap on `INT`. Rejected because it misses `TERM`, hangup, and clean exit.

- **Prefixed interleaved output via per-process output redirection to a `while read` loop.**
  - Rationale: bash `>` redirection into a `while read` loop running `printf '[%s] %s\n' "$name" "$line"` is the simplest reliable way to prefix every line of a child's stdout/stderr with the service name. Preserves line ordering within each stream; interleaving between streams is non-deterministic but acceptable for dev output.
  - Alternative considered: tmux/iterm split panes. Rejected — adds a dependency and reduces portability.

- **Keep `reload=True` in `vela_api.cli`.**
  - Rationale: hot reload is a productivity win worth the cleanup complexity, and the orchestrator now handles that complexity. Removing reload would force a manual restart on every code change.
  - Alternative considered: drop `reload=True` and remove the cleanup. Rejected — reload is valuable.

- **No `npm install` step in the script.**
  - Rationale: first-run install is slow (tens of seconds) and only happens once per checkout; baking it into the script would slow every subsequent run. If `node_modules` is missing, vite's error message is clear enough.
  - Alternative considered: `npm --prefix apps/web install` if `node_modules` is absent. Deferred — easy to add later if needed.

- **No `uv sync` step in the script.**
  - Rationale: `uv run` already ensures the env is up to date for the requested command. Same rationale as npm.
  - Alternative considered: explicit `uv sync` upfront. Deferred.

## Risks / Trade-offs

- **Misidentification risk on busy multi-user hosts.** If two developers run the script on the same machine and target different checkouts, PID files in shared `/tmp` could collide by name (not by content) and one developer's script could try to kill the other's process. Mitigation: PID file names are unique per service; collision requires both to be on the same service at the same time, which is rare in practice. Acceptable for local dev; can be tightened later by hashing the repo path into the PID filename.
- **Race between `lsof` and `ps` in `cleanup_old`.** Between identifying a PID and reading its command line, the PID could be reused by another process. Mitigation: extremely small window on macOS/Linux PIDs (typical reuse requires PIDs to wrap); in practice the script reads ps immediately after lsof. Acceptable.
- **Subprocess output buffering.** Without `stdbuf -oL` or `unbuffer`, Python (uvicorn) can buffer stdout when not attached to a TTY, making lines appear in bursts. The `while read` redirection does not change this. Mitigation: if it becomes annoying, set `PYTHONUNBUFFERED=1` for the uvicorn child. Deferred — observe first.
- **Multi-terminal concurrent runs.** Two terminals running the script at once could each try to kill the other on startup. The kill-by-command-line scope prevents accidentally killing unrelated services, but two instances of the script would still race. Mitigation: not blocking for the stated one-terminal usage pattern; if multi-terminal becomes routine, add a `flock` on `/tmp/vela-dev.lock` to serialize startup. Deferred.
- **Grace period is a fixed 5s.** A genuinely long-running request (e.g. an in-flight backtest) gets SIGKILLed at 5s, leaving the SQLite WAL potentially mid-transaction. Mitigation: SQLite WAL is robust to this — the transaction rolls back on next open. Acceptable for local dev.
- **Script is macOS/Linux only.** Windows developers need a `.ps1` equivalent. Documented as out of scope; can be added if the team grows.