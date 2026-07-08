#!/usr/bin/env bash
# scripts/dev.sh
#
# One-shot local development orchestrator for Vela.
#
# What it does:
#   1. Precheck: refuse to start if `uv` or `npm` is missing on PATH.
#   2. Cleanup:  for each of API_PORT (8000) and WEB_PORT (5173), find PIDs
#                bound to that port and SIGTERM only those whose command line
#                contains the expected identity substring. Wait up to 5s, then
#                SIGKILL any survivors. Unrelated services on the same ports
#                are left alone.
#   3. Launch:   start `uv run vela-api` and `npm --prefix apps/web run dev`
#                in the background, redirect each child's stdout+stderr
#                through a `while read` loop that prefixes every line with
#                [vela-api] or [vela-web], and write each child's PID to
#                /tmp/vela-{api,web}.pid.
#   4. Wait:     poll the two child PIDs so any child exit (clean crash,
#                Ctrl+C in a real terminal, SIGTERM, or natural death)
#                reaches the script's end and triggers the EXIT trap,
#                which tears both children down with the same two-phase
#                shutdown used at startup.
#
# Kill scope is port + command-line match, not PID file alone, so a stale
# orphan from a crashed previous session is still recovered even when its
# PID file is missing or wrong.

set -euo pipefail

# This script uses `set -o pipefail`, `local`, arrays, process
# substitution, and C-style `for ((;;))` arithmetic. All of those are
# bash 2.04+; we enforce 3.2+ as a safe floor because macOS /bin/bash
# ships at 3.2.57 and we want a clear error on dash/ash/POSIX sh.
if [ -z "${BASH_VERSION:-}" ] || [ "${BASH_VERSINFO[0]:-0}" -lt 3 ] || \
   { [ "${BASH_VERSINFO[0]:-0}" -eq 3 ] && [ "${BASH_VERSINFO[1]:-0}" -lt 2 ]; }; then
  printf '[dev.sh] this script requires bash 3.2+; do not run it via sh/dash/ash\n' >&2
  exit 1
fi

# Signal-handling note for non-interactive bash: bash's non-interactive
# mode ignores SIGINT at startup. The `trap 'shutdown' INT` line below
# only takes effect when bash is interactive OR when SIGINT is delivered
# to a process group that includes the script's children (which uvicorn
# and vite do handle cleanly). In practice this means:
#   - Running `./scripts/dev.sh` in a real terminal and pressing Ctrl+C:
#     the terminal sends SIGINT to the foreground process group; uvicorn
#     and vite receive it and exit; dev.sh's polling loop detects the
#     children are gone, the script reaches its end, and the EXIT trap
#     fires `shutdown`. Net result is the same as if the INT trap had
#     fired directly.
#   - Sending `kill -TERM $PID` from another shell: the TERM trap fires
#     and `shutdown` runs synchronously. This is the canonical way to
#     stop a backgrounded dev.sh from a second terminal.
#   - Sending `kill -INT $PID` from another shell to a non-interactive
#     dev.sh: the signal is ignored by bash itself, the children are not
#     in the same process group, and nothing happens. Use SIGTERM.

# --- Configuration ---------------------------------------------------------

API_PORT=8000
WEB_PORT=5173
API_PID=/tmp/vela-api.pid
WEB_PID=/tmp/vela-web.pid

API_NAME=vela-api
WEB_NAME=vela-web

# Command-line substrings used to decide whether a process bound to the
# port is "ours". A match against the substring is required before any
# signal is sent.
#
# The API match accepts BOTH `vela-api` (the console-script name from
# `pyproject.toml`, what `uv run vela-api` invokes) and `vela_api` (the
# Python module name, what `uv run uvicorn vela_api.main:app` shows).
# In practice the reloader parent shows `vela-api` on the command line
# while a directly-invoked uvicorn shows `vela_api.main:app`; both must
# be recognized. The reloader child spawned via `multiprocessing.spawn`
# does NOT carry either substring in its command line, so it is reached
# transitively by killing the reloader parent (uvicorn propagates
# SIGTERM to the worker).
API_MATCH='vela-api|vela_api'
WEB_MATCH=vite

# Grace period for two-phase shutdown (SIGTERM -> wait -> SIGKILL).
GRACE_SECONDS=5
GRACE_TICKS=10        # GRACE_SECONDS * (1 / POLL_INTERVAL)
POLL_INTERVAL=0.5     # seconds between kill -0 polls

# --- Helpers ---------------------------------------------------------------

log() {
  printf '[dev.sh] %s\n' "$*"
}

# usage: die <message...>
die() {
  printf '[dev.sh] %s\n' "$*" >&2
  exit 1
}

# usage: require_cmd <command>
require_cmd() {
  local cmd=$1
  if ! command -v "$cmd" >/dev/null 2>&1; then
    die "required command '$cmd' is not on PATH; install it before running $0"
  fi
}

# usage: send_signal <pid> <signal>
send_signal() {
  local pid=$1 signal=$2
  # kill -0 handles "process gone" via the && short-circuit; we want to
  # silently skip the signal in that case.
  if kill -0 "$pid" 2>/dev/null; then
    kill "$signal" "$pid" 2>/dev/null || true
  fi
}

# usage: wait_for_exit <pid> <max_seconds>
#
# Coarse-grained poll used by `shutdown_child`. Kept as a separate
# function for the shutdown path because there we have at most one
# child per call and a 1-second tick is plenty.
wait_for_exit() {
  local pid=$1 max=$2
  local i=0
  while [ "$i" -lt "$max" ]; do
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  return 1
}

# usage: kill_matched <port> <match_substr>
#
# Lists PIDs listening on $port, sends SIGTERM to those whose command line
# contains $match_substr, waits up to GRACE_SECONDS for them to exit, then
# SIGKILLs any survivors. Returns 0 always; callers do not branch on
# "did we kill anything" — they only care that the port is now free (or
# that an unrelated process is still there, which is fine).
kill_matched() {
  local port=$1 match=$2
  local pids=() pid cmd

  # lsof exits non-zero when nothing is bound; that's expected.
  while IFS= read -r pid; do
    [ -n "$pid" ] || continue
    pids+=("$pid")
  done < <(lsof -ti:"$port" 2>/dev/null || true)

  if [ "${#pids[@]}" -eq 0 ]; then
    return 0
  fi

  log "port $port: candidates from lsof: ${pids[*]} (match='$match')"

  # Phase 1: SIGTERM matched PIDs. The match string is treated as an
  # extended regular expression: `vela-api|vela_api` matches either
  # substring. `[[ =~ ]]` is bash 3.2+ and supports ERE alternation
  # directly, which is why we don't use a case-statement glob here
  # (case globs are single-pattern, not regex).
  local matched=()
  for pid in "${pids[@]}"; do
    cmd=$(ps -p "$pid" -o command= 2>/dev/null || true)
    if [[ "$cmd" =~ $match ]]; then
      log "  SIGTERM $pid ($cmd)"
      send_signal "$pid" -TERM
      matched+=("$pid")
    else
      log "  skip   $pid (does not match '$match'): $cmd"
    fi
  done

  if [ "${#matched[@]}" -eq 0 ]; then
    return 0
  fi

  # Wait for them to exit, polled in finer-grained slices so a fast exit
  # does not pay the full grace window. Per-PID liveness is checked
  # with `kill -0`; the loop breaks early the moment all matched PIDs
  # are gone.
  local alive_count
  for ((tick=0; tick<GRACE_TICKS; tick++)); do
    alive_count=0
    for pid in "${matched[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then
        alive_count=$((alive_count + 1))
      fi
    done
    if [ "$alive_count" -eq 0 ]; then
      log "  all matched exited within grace window"
      return 0
    fi
    sleep "$POLL_INTERVAL"
  done

  # Phase 2: SIGKILL survivors.
  for pid in "${matched[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      log "  SIGKILL $pid (still alive after ${GRACE_SECONDS}s)"
      send_signal "$pid" -KILL
    fi
  done

  # Brief settle so the kernel releases the port before we relaunch.
  sleep 0.2
  return 0
}

# usage: start_service <name> <pidfile> <cmd...>
#
# Launches <cmd...> in the background with stdout+stderr merged and
# redirected through a `while read` loop that prefixes every line with
# [name]. Writes the launched child PID to <pidfile>. Performs a brief
# liveness check after launch so missing executables or a broken venv
# fail fast with a clear error rather than leaving the script hanging
# in `wait` for a process that exited in the first few hundred ms.
start_service() {
  local name=$1 pidfile=$2
  shift 2
  local cmd=( "$@" )

  # Replace any stale pidfile from a previous run; we re-discover the
  # actual child via lsof at startup, so a wrong PID is harmless, but
  # a missing one is also harmless — start with a clean slate.
  rm -f "$pidfile"

  log "starting $name: ${cmd[*]}"

  # The `(... )` runs the while loop in a subshell so its `read` does not
  # mutate the parent's IFS / positional params. `2>&1` merges stderr into
  # stdout so a single read loop sees both. The `&` backgrounds the whole
  # pipeline; $! is the PID of the subshell, which we do NOT want — we
  # want the inner exec'd process. Using `exec "$@"` inside the subshell
  # replaces the subshell with the real command so $! in *this* subshell
  # becomes the child PID we care about. (Bash $! after `&` reports the
  # immediate child's PID, which here is the subshell that then execs.)
  ( exec "${cmd[@]}" ) > >(
    while IFS= read -r line; do
      printf '[%s] %s\n' "$name" "$line"
    done
  ) 2>&1 &

  local child_pid=$!
  echo "$child_pid" > "$pidfile"
  log "$name started, pid=$child_pid, pidfile=$pidfile"

  # Liveness check: most crash modes (command not found, venv missing,
  # bad path) exit within a few hundred ms. If the child is already
  # gone, fail loudly with a clear message and let the trap clean up
  # the other child.
  sleep 0.4
  if ! kill -0 "$child_pid" 2>/dev/null; then
    die "$name: child process exited within 0.4s of launch (pid $child_pid); check that '${cmd[*]}' is runnable"
  fi
}

# usage: shutdown_child <pidfile>
#
# Sends SIGTERM to the PID stored in <pidfile>, waits up to GRACE_SECONDS,
# then SIGKILLs any survivor. Removes the pidfile. Tolerates a missing
# file or stale PID (process already gone) without error.
shutdown_child() {
  local pidfile=$1
  [ -f "$pidfile" ] || return 0
  local pid
  pid=$(cat "$pidfile" 2>/dev/null || true)
  rm -f "$pidfile"
  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi

  log "shutdown: SIGTERM $pid (from $pidfile)"
  send_signal "$pid" -TERM
  if wait_for_exit "$pid" "$GRACE_SECONDS"; then
    return 0
  fi
  log "shutdown: SIGKILL $pid (still alive after ${GRACE_SECONDS}s)"
  send_signal "$pid" -KILL
  # Best-effort reap; do not loop.
  wait "$pid" 2>/dev/null || true
}

shutdown() {
  # Run in subshell-safe order: children first, then any remaining
  # cleanup. Failures inside the trap must not abort the trap itself.
  local exit_code=$?
  set +e
  shutdown_child "$API_PID"
  shutdown_child "$WEB_PID"
  exit "$exit_code"
}

# --- Main ------------------------------------------------------------------

require_cmd uv
require_cmd npm
require_cmd lsof
require_cmd ps

# Trap once, after functions are defined and after we've recorded the
# child PIDs (so a misbehaving tool that signals us before launch is
# complete cannot trigger a shutdown against empty pidfiles).
trap 'shutdown' EXIT INT TERM

log "preflight: cleaning any stale Vela-owned processes"
kill_matched "$API_PORT" "$API_MATCH"
kill_matched "$WEB_PORT" "$WEB_MATCH"

start_service "$API_NAME" "$API_PID" uv run vela-api
start_service "$WEB_NAME" "$WEB_PID" npm --prefix apps/web run dev

# Block here until either child exits, then let the EXIT trap fire and
# tear down the surviving sibling. We poll instead of using `wait` so
# a child that exits cleanly (status 0) also triggers shutdown — `wait`
# with no args waits for ALL background children and would leave the
# orchestrator alive on the surviving sibling. `wait -n` would be the
# clean fix, but macOS /bin/bash is 3.2 and lacks it.
api_pid=$(cat "$API_PID" 2>/dev/null || echo "")
web_pid=$(cat "$WEB_PID" 2>/dev/null || echo "")
log "both services started; tail the unified log above, Ctrl+C to stop"
while :; do
  for pid in "$api_pid" "$web_pid"; do
    [ -n "$pid" ] || continue
    if ! kill -0 "$pid" 2>/dev/null; then
      break 2
    fi
  done
  sleep 0.2
done
# Falling out of the loop means at least one child exited; let the
# EXIT trap run shutdown and exit.
