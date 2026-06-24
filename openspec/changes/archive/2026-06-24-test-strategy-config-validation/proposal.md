## Why

COP-67 requires stronger automated coverage for strategy configuration validation. The existing schema and loader already reject invalid strategy configs, but several tests only assert that validation fails, not which field or message failed, which leaves the validation contract harder to maintain.

## What Changes

- Add focused tests for valid and invalid strategy configuration inputs.
- Assert validation failure messages for representative invalid schema and loader cases.
- Preserve the existing strategy configuration schema and YAML format.
- Keep runtime behavior unchanged unless tests expose an existing mismatch with the specification.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `strategy-configuration`: Clarify that strategy configuration validation failures expose assertable field-specific error messages.

## Impact

- Affected tests: `packages/core/tests/test_strategy_config.py`
- Affected specs: `openspec/specs/strategy-configuration/spec.md`
- No database migration, CLI command, API endpoint, config file format change, or external dependency is introduced.
