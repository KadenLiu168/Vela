## Why

AkShare source calls can fail transiently during market data ingestion, causing an otherwise recoverable run to be recorded as failed or partial. COP-37 adds a small, explicit retry policy so temporary data source failures get a limited second chance while final failures still remain visible in fetch logs.

## What Changes

- Add `tenacity` as the retry dependency for data source calls.
- Retry transient AkShare source call failures with a simple, finite policy.
- Preserve the existing provider-level error behavior when all retry attempts fail.
- Keep normalization and validation failures non-retried because invalid returned data is not a transient source-call failure.
- Keep existing market data fetch logging semantics so final failures are still recorded by `DataFetchLog`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `market-data-provider`: Add retry behavior for transient AkShare source call failures while preserving provider-level errors after retry exhaustion.

## Impact

- `pyproject.toml` and `uv.lock`: add the `tenacity` runtime dependency.
- `packages/core/src/vela_core/akshare_market_data_provider.py`: wrap only the AkShare source call with the retry policy.
- `packages/core/tests/test_akshare_market_data_provider.py`: add focused retry tests for eventual success, exhausted retries, and non-retried invalid data.
- Existing fetch workflow and CLI behavior remain unchanged; final provider failures continue to flow into existing failed or partial `DataFetchLog` records.
