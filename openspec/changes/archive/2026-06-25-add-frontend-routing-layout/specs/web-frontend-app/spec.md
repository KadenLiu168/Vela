## ADDED Requirements

### Requirement: Frontend route placeholders
The web frontend SHALL provide client-side route placeholders for the Dashboard, Signal Detail, and Backtest Detail page areas.

#### Scenario: Dashboard route renders
- **WHEN** a developer opens the web frontend at `/`
- **THEN** the app renders the Dashboard page area

#### Scenario: Signal detail route renders
- **WHEN** a developer opens the web frontend at `/signals/demo-signal`
- **THEN** the app renders a Signal Detail page placeholder for `demo-signal`

#### Scenario: Backtest detail route renders
- **WHEN** a developer opens the web frontend at `/backtests/demo-backtest`
- **THEN** the app renders a Backtest Detail page placeholder for `demo-backtest`

### Requirement: Local research workflow layout
The web frontend SHALL render a base layout for a local research workflow tool with navigation to Dashboard, Signal Detail, and Backtest Detail.

#### Scenario: First screen is the workflow dashboard
- **WHEN** a developer opens the default web frontend route
- **THEN** the first screen presents workflow dashboard content instead of marketing, login, or deployment content

#### Scenario: Navigation exposes research page areas
- **WHEN** a developer inspects the base layout navigation
- **THEN** it provides entries for Dashboard, Signal Detail, and Backtest Detail

### Requirement: Local-only frontend structure
The web frontend SHALL avoid login, multi-user, account management, and production deployment entry points in the base layout and route placeholders.

#### Scenario: Layout remains local-tool focused
- **WHEN** a developer inspects the rendered base layout and route placeholders
- **THEN** they do not include login, signup, account switching, team management, hosting, or production deployment actions
