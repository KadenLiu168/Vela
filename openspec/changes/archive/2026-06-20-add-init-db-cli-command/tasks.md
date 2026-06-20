## 1. Tests

- [x] 1.1 Add CLI test coverage for initializing a missing temporary SQLite database with `init-db`.
- [x] 1.2 Add CLI test coverage that running `init-db` twice against the same database succeeds both times.
- [x] 1.3 Add CLI test coverage for failed initialization output and non-zero exit status.

## 2. CLI Implementation

- [x] 2.1 Add the minimal CLI module structure under `apps/cli` for dispatching the `init-db` command.
- [x] 2.2 Implement `init-db` by running Alembic `upgrade head` against the selected database URL.
- [x] 2.3 Register the project CLI entrypoint in `pyproject.toml`.
- [x] 2.4 Ensure success output identifies the initialized database target and failure output includes useful error context.

## 3. Documentation

- [x] 3.1 Document the local development `init-db` command in the CLI README or project README.

## 4. Verification

- [x] 4.1 Run the focused CLI tests.
- [x] 4.2 Run the project test suite or nearest practical test command.
- [x] 4.3 Run `openspec status --change "add-init-db-cli-command"` and confirm the change is ready for implementation tracking.
