## Why

The backend needs a consistent logging baseline before application entrypoints, data jobs, and tests grow further. A shared logging setup avoids ad hoc formatter and level choices across packages.

## What Changes

- Add a reusable logging configuration module.
- Provide a `setup_logging()` function for initializing application logging.
- Support basic log level configuration.
- Apply one consistent log message format across configured handlers.
- Add tests covering default behavior, custom level behavior, and formatting expectations.

## Capabilities

### New Capabilities
- `logging-configuration`: Defines the shared backend logging setup contract, including initialization, log level selection, and unified formatting.

### Modified Capabilities

## Impact

- Affects reusable backend package code under `packages/`.
- Adds focused unit tests for logging configuration behavior.
- No new runtime dependencies are expected.
