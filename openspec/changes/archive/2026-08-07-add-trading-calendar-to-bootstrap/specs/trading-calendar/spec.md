## ADDED Requirements

### Requirement: Trading calendar sync is part of local setup bootstrap
The trading calendar sync workflow SHALL be invoked by the `run_local_setup_bootstrap` orchestration as a bootstrap step named `sync_trading_calendar`, positioned after the ETF pool sync and before the full market-data fetch. The bootstrap step SHALL call the existing `sync_trading_calendar_to_db` workflow with default arguments and SHALL report its result through the standard `BootstrapStepResult` status, duration, and error-message fields. The bootstrap step SHALL NOT duplicate the akshare fetch, parse, or upsert logic of `sync_trading_calendar_to_db`.

#### Scenario: Bootstrap step reuses the sync workflow
- **WHEN** `run_local_setup_bootstrap` reaches the trading-calendar step
- **THEN** the step invokes `vela_core.trading_calendar_sync.sync_trading_calendar_to_db` against the bootstrap session
- **AND** does not call akshare or upsert trading days through any other code path

#### Scenario: Bootstrap step surfaces sync failure without raising
- **WHEN** `sync_trading_calendar_to_db` returns `status = "failed"` during a bootstrap run
- **THEN** the bootstrap step records `status = "failed"` with the sync result's error message
- **AND** does not propagate the failure as an exception to the bootstrap caller
