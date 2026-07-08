# Tasks

## 1. Script Skeleton

- [x] 1.1 Create `scripts/dev.sh` with `#!/usr/bin/env bash`, `set -euo pipefail`, and named constants `API_PORT=8000`, `WEB_PORT=5173`, `API_PID=/tmp/vela-api.pid`, `WEB_PID=/tmp/vela-web.pid`.
- [x] 1.2 Add a precheck that fails fast with a clear message if `uv` or `npm` is missing (`command -v`).

## 2. Cleanup Helper

- [x] 2.1 Implement `cleanup_old(port, label, match_substr)` that lists PIDs via `lsof -ti:"$port"`, inspects each with `ps -p $pid -o command=`, and only sends `SIGTERM` to those whose command line contains `match_substr`.
- [x] 2.2 Loop for up to 5 seconds (10 × 0.5s) waiting for the matched PIDs to exit; re-check via `kill -0`.
- [x] 2.3 Send `SIGKILL` to any matched PIDs still alive after the grace window.
- [x] 2.4 Call `cleanup_old "$API_PORT" api vela_api` and `cleanup_old "$WEB_PORT" web vite` at the top of the script, in that order.

## 3. Child Launch + Prefixed Output

- [x] 3.1 Implement `start_service(name, pidfile, cmd...)` that removes any stale pidfile, launches the command with `&`, and redirects stdout+stderr through a `while IFS= read -r line; do printf '[%s] %s\n' "$name" "$line"; done` loop.
- [x] 3.2 After launching, write `$!` to the pidfile.
- [x] 3.3 Call `start_service vela-api "$API_PID" uv run vela-api` and `start_service vela-web "$WEB_PID" npm --prefix apps/web run dev`.

## 4. Trap-Based Shutdown

- [x] 4.1 Register a single `trap 'shutdown' EXIT INT TERM` that sends `SIGTERM` to the PIDs in `$API_PID` and `$WEB_PID` (ignoring missing-file / missing-process errors).
- [x] 4.2 Inside `shutdown`, sleep up to 5 seconds waiting for both children to exit (`kill -0` checks in a loop).
- [x] 4.3 Send `SIGKILL` to any survivors; remove both pidfiles.

## 5. Foreground Wait

- [x] 5.1 End the script with a bare `wait` so the parent shell blocks until either child exits (which then triggers the EXIT trap and tears down both).

## 6. Documentation

- [x] 6.1 Create or update `scripts/README.md` describing what `dev.sh` does, the kill scope (port + command-line match), and how to run it.
- [x] 6.2 Add a short cross-reference paragraph to `apps/web/README.md` pointing developers at `scripts/dev.sh` as the canonical way to start the local stack.
- [x] 6.3 Add a short cross-reference paragraph to the API side (root `README.md` developer workflow section). `apps/api/README.md` already exists but only documents the API package itself, so the canonical developer-workflow pointer lives at the repo root.

## 7. Manual Verification

- [x] 7.1 `chmod +x scripts/dev.sh` and verify `./scripts/dev.sh` from the repo root starts both services with prefixed output.
- [x] 7.2 Verify that an existing `uv run vela-api` (running in another terminal) is killed on the next `./scripts/dev.sh` startup, freeing port 8000.
- [x] 7.3 Verify that an unrelated service bound to 8000 (e.g. a dummy Python `http.server`) is NOT killed by the script.
- [x] 7.4 Send `Ctrl+C` to the running script and confirm both processes exit within the 5s grace window and pidfiles are removed.

## 8. OpenSpec Validation

- [x] 8.1 Run `openspec validate 2026-07-08-add-dev-orchestration-script --strict` and resolve any reported issues.