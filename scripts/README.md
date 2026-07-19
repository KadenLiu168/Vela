# scripts

Development and automation scripts for the Vela repository.

## Generate the Inter Variable subset

The committed public webfont is generated from the vendored Inter 4.0 source,
its reviewed Unicode manifest, and the locked FontTools WOFF2 toolchain. From
the repository root, regenerate it with:

```bash
uv run python scripts/fonts/inter/subset_inter_variable.py
```

The script verifies the canonical source SHA-256 and fails if the generated
font exceeds the 98,304-byte budget. Pass an optional output path to generate
into a temporary location for validation without overwriting the public asset.

## dev.sh — local dev orchestrator

`scripts/dev.sh` is the canonical way to start the full Vela local stack
in one terminal. From the repo root:

```bash
./scripts/dev.sh
```

It launches the FastAPI backend (`uv run vela-api` on port 8000) and the
Vite dev server (`npm --prefix apps/web run dev` on port 5173) together
in the background, with their logs interleaved in your terminal and
each line prefixed by `[vela-api]` or `[vela-web]`.

Press `Ctrl+C` to stop both services.

### Why this exists

`uv run vela-api` calls `uvicorn.run(..., reload=True)`, which spawns a
reloader parent plus a server child. When `Ctrl+C` does not propagate
cleanly through the reloader, the child stays bound to port 8000 and the
next `uv run vela-api` aborts with `Address already in use`. The
orchestrator solves this with two mechanisms:

1. **Startup cleanup** — before launching, it scans ports 8000 and 5173
   for processes whose command line contains `vela_api` (port 8000) or
   `vite` (port 5173), sends them SIGTERM, waits up to 5 seconds, then
   SIGKILLs any survivors.
2. **Single-terminal shutdown** — a `trap` on `EXIT INT TERM` performs
   the same two-phase shutdown on both children whenever the parent
   script exits, so a child crash or `Ctrl+C` never leaves a zombie.

### Kill scope

The cleanup matches on **port + command-line identity**, not just port.
Concretely:

- Port 8000 candidates are only killed if `ps -o command=` for the PID
  contains the substring `vela_api`.
- Port 5173 candidates are only killed if the command line contains
  the substring `vite`.

An unrelated process bound to either port (a debug proxy, a second web
server, etc.) is left alone. The orchestrator will not silently take
down something it does not own.

### PID files

Each spawned child is recorded in `/tmp`:

- `/tmp/vela-api.pid` — the FastAPI backend (after `uv run` exec)
- `/tmp/vela-web.pid` — the Vite dev server

These files are used at shutdown to send SIGTERM to the right PIDs and
are removed when the script exits. They are also removed and recreated
on every launch, so a stale PID from a crashed previous run never
interferes.

### Limitations

- macOS / Linux only. There is no Windows `.ps1` equivalent in this
  change. The script depends on `lsof`, `ps`, and POSIX signals.
- One terminal per orchestrator instance. Two terminals running
  `./scripts/dev.sh` at once will race to kill each other's stale
  children on startup. For multi-terminal use, run them at different
  times or in a single terminal via `tmux` panes.
- PID files in `/tmp/vela-api.pid` and `/tmp/vela-web.pid` use fixed
  names. On a shared multi-user host, two users running the
  orchestrator from different checkouts could overwrite each other's
  pidfiles. The startup cleanup uses `lsof` (not the pidfile) to find
  stale processes, so the port-conflict recovery still works; the only
  failure mode is that the second user's shutdown handler could try
  to `kill` a PID that is no longer theirs. In practice this requires
  a rare PID-collision event. Tightening this would require hashing
  the repo path into the pidfile name.
- The orchestrator does not run `uv sync` or `npm install` — those
  remain manual one-time setup steps.
- A child process that exits within the first 0.4 s of launch (e.g.
  `uv` not in a synced venv, `node_modules` missing) is treated as a
  failed start and the script exits non-zero with a clear message
  rather than hanging in `wait`.
