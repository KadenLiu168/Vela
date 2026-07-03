## ADDED Requirements

### Requirement: Frontend visual consistency QA
The web frontend SHALL keep the Dashboard, Signal Detail, Backtest Detail, AppShell navigation, tables, cards, forms, buttons, and feedback states visually aligned with `DESIGN.md`.

#### Scenario: Required frontend routes pass visual QA
- **WHEN** a developer inspects `/`, `/signals/demo-signal`, and `/backtests/1`
- **THEN** the visible UI uses the established graphite, canvas, ash, fog, ivory, ember, and brass design tokens instead of a blue or green default admin palette
- **AND** buttons, cards, tables, forms, navigation, and feedback states use consistent tokenized radius, typography, spacing, and surface treatments

#### Scenario: Required frontend routes remain readable on mobile
- **WHEN** a developer inspects `/`, `/signals/demo-signal`, and `/backtests/1` in a mobile viewport
- **THEN** the page header, navigation, action controls, content cards, forms, tables, and feedback states do not visibly overlap, clip, or become unreadable

#### Scenario: Visual QA does not change application behavior
- **WHEN** the frontend visual QA pass is implemented
- **THEN** existing business logic, API calls, and route structure remain unchanged
- **AND** the frontend does not add a large UI framework or new production dependency
