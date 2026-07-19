## ADDED Requirements

### Requirement: CLI generate signal accepts provenance source

The `generate-signal` command SHALL accept an optional `--source` argument restricted to `manual` or `scheduled`, default it to `manual`, and forward the resolved value to `generate_and_persist_strategy_signal`.

#### Scenario: CLI defaults source to manual
- **WHEN** a user invokes `generate-signal` without `--source`
- **THEN** the persisted signal has `source="manual"`
- **AND** existing command output and exit-status behavior are unchanged

#### Scenario: CLI records scheduled source
- **WHEN** an automated caller invokes `generate-signal --source scheduled`
- **THEN** the persisted signal has `source="scheduled"`

#### Scenario: CLI rejects unsupported source
- **WHEN** a user invokes `generate-signal` with `--source backtest`, `--source legacy`, or another unsupported value
- **THEN** argument parsing fails without generating or persisting a signal
