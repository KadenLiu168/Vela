## REMOVED Requirements

### Requirement: API caches loaded strategy config
**Reason**: The startup-frozen `app.state.strategy_config` is only consumed by the Bootstrap endpoint and causes edits made during the API process lifetime to be ignored. `GET /api/config` already loads the current files per request, so the requirement's shared-instance scenario does not describe the current architecture.

**Migration**: Remove `app.state.strategy_config`. `POST /api/setup/bootstrap` loads one `AppConfig` at the start of each request, as specified by `local-setup-bootstrap`; other config-consuming endpoints keep their existing per-request loading behavior.
