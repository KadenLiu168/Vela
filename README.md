# Vela

Vela is a personal ETF rotation system focused on strategy research, signal generation, and historical backtesting.

## Project Goals

- Fetch and normalize ETF market data
- Store ETF metadata and historical prices
- Generate ETF rotation strategy signals
- Run historical backtests
- Provide a clean backend foundation for future API, CLI, and UI layers

## Repository Structure

```text
apps/       Application entrypoints, such as API and CLI
packages/   Reusable business packages
openspec/   Project specifications and change proposals
scripts/    Development and automation scripts
tests/      Repository-level integration tests
docs/       Architecture and design documents
