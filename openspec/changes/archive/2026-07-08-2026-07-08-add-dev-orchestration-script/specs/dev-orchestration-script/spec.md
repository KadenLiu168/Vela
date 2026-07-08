## ADDED Requirements

### Requirement: Dev orchestration script starts backend and frontend together
The system SHALL provide a `scripts/dev.sh` script that, when run from the repo root, cleans stale Vela-owned processes on ports 8000 (FastAPI / uvicorn) and 5173 (Vite) and then launches `uv run vela-api` and `npm --prefix apps/web run dev` together in the same terminal with prefixed, interleaved output.

#### Scenario: Clean startup launches both services
- **WHEN** a developer runs `./scripts/dev.sh` from the repo root with no previous Vela processes running on 8000 or 5173
- **THEN** the script starts the FastAPI backend on port 8000 via `uv run vela-api`
- **AND** the script starts the Vite dev server on port 5173 via `npm --prefix apps/web run dev`
- **AND** the script's stdout and stderr show both services' logs interleaved with a `[vela-api]` or `[vela-web]` line prefix

#### Scenario: Precheck fails fast when uv or npm is missing
- **WHEN** a developer runs `./scripts/dev.sh` and `uv` or `npm` is not on `PATH`
- **THEN** the script exits non-zero with a clear message naming the missing tool
- **AND** the script does not attempt to start either service

### Requirement: Stale-process cleanup is scoped to Vela-owned command lines
The system SHALL scope the startup cleanup so that only processes whose command line matches a Vela-owned identifier are killed, leaving any unrelated service bound to those ports untouched. For port 8000 the match is the regex `vela-api|vela_api` (so the `vela-api` console-script invocation and a direct `uv run uvicorn vela_api.main:app` both match); for port 5173 the match is the literal `vite`.

#### Scenario: Vela-owned orphan on 8000 is killed
- **WHEN** a developer runs `./scripts/dev.sh` and a previous `uv run vela-api` is still bound to 8000
- **THEN** the cleanup phase sends SIGTERM to the reloader parent process (its command line contains the `vela-api` console-script path)
- **AND** uvicorn's reloader propagates the signal to its worker child so the port is released
- **AND** the script then starts a fresh `uv run vela-api` that successfully binds 8000

#### Scenario: Unrelated process on 8000 is left alone
- **WHEN** a developer runs `./scripts/dev.sh` and a process bound to 8000 has a command line that does not match `vela-api|vela_api` (e.g. a debug `http.server`)
- **THEN** the cleanup phase does not send any signal to that process
- **AND** the script surfaces a clear error in the prefixed output when the fresh `uv run vela-api` subsequently fails to bind 8000

#### Scenario: Graceful shutdown escalates to SIGKILL
- **WHEN** the cleanup phase sends SIGTERM to a matched PID
- **THEN** it waits up to 5 seconds for that PID to exit (re-checked via `kill -0`)
- **AND** sends SIGKILL to any matched PID still alive after the grace window

### Requirement: Two-phase shutdown of children on script exit
The system SHALL terminate both child processes cleanly when the orchestration script exits, regardless of whether the exit is triggered by `Ctrl+C` (SIGINT) in a real terminal, `SIGTERM` from another shell, or natural completion of one of the children.

#### Scenario: Ctrl+C in a real terminal tears down both children within 5 seconds
- **WHEN** a developer presses `Ctrl+C` while `./scripts/dev.sh` is running in a real terminal
- **THEN** the terminal sends SIGINT to the foreground process group, which uvicorn and vite handle by exiting
- **AND** the script's polling loop detects the children are gone and the script reaches its end
- **AND** the EXIT trap fires `shutdown`, which removes `/tmp/vela-api.pid` and `/tmp/vela-web.pid`
- **AND** both ports 8000 and 5173 are released within 5 seconds

#### Scenario: SIGTERM to the orchestrator tears down both children within 5 seconds
- **WHEN** `kill -TERM $PID` is sent to a running `./scripts/dev.sh` from another shell
- **THEN** the SIGTERM trap fires `shutdown`, which sends SIGTERM to both child processes
- **AND** `shutdown` waits up to 5 seconds for each child to exit
- **AND** sends SIGKILL to any child still alive after the grace window
- **AND** removes `/tmp/vela-api.pid` and `/tmp/vela-web.pid`

#### Scenario: A child exit triggers cleanup of the other
- **WHEN** the FastAPI backend child exits (e.g. crashes) while the Vite frontend child is still running
- **THEN** the script's polling loop detects the backend child is gone, the script reaches its end
- **AND** the EXIT trap fires and tears down the surviving Vite child via the same two-phase shutdown
- **AND** the script itself exits

### Requirement: Per-child PID tracking in /tmp
The system SHALL record the PID of each spawned child in `/tmp/vela-api.pid` and `/tmp/vela-web.pid` immediately after launch, and remove those files on shutdown.

#### Scenario: PID file is written on launch
- **WHEN** the script starts a service
- **THEN** the corresponding `/tmp/vela-*.pid` file exists and contains the child PID

#### Scenario: Stale PID file is replaced
- **WHEN** the script starts a service and a previous `/tmp/vela-*.pid` file exists
- **THEN** the stale file is removed before the new child is launched
- **AND** the file is rewritten with the new child's PID

#### Scenario: PID files are removed on shutdown
- **WHEN** the script's shutdown handler runs
- **THEN** `/tmp/vela-api.pid` and `/tmp/vela-web.pid` are both removed
- **AND** missing-file errors during removal are ignored
