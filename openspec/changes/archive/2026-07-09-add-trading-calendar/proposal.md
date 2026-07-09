## Why

Phase 2 交易日缺口检测需要一个“参照系”——哪些日子本该有数据。当前代码库没有任何交易日历（无 calendar 表/模型、无 `exchange_calendars` 依赖、未调用 akshare 的日历接口）。A 股节假日把工作日变成休市日（国庆、春节、调休），Weekday 启发式会把 10/8 这种假期当成“应有数据的交易日”而误报；要准确只能用真日历。

akshare 已是项目默认依赖，其 `tool_trade_date_hist_sina()` 接口返回 1990-12-19 起的全部 A 股交易日。本变更新增 `trading_calendar` 表与同步流程，作为**纯数据基础设施**，为后续缺口检测 change 提供权威参照系。本变更不含任何检测逻辑。

## What Changes

- 新增 `trading_calendar` 表：`trade_date` 为主键，记录每个交易日；附带 `source`（数据来源）与时间戳，与项目其他表风格一致。
- 新增 `TradingCalendar` ORM 模型。
- 新增 `trading_calendar_sync.py` 同步模块：`sync_trading_calendar_to_db(session)` 调用 akshare `tool_trade_date_hist_sina`，解析返回的交易日并 upsert 到 `trading_calendar` 表，返回 `TradingCalendarSyncResult`（含 inserted/updated 计数与 status）。
- 新增 CLI 命令 `vela sync-trading-calendar`（参照现有 `sync-etf-pool` 模式）。
- alembic 迁移 `0009`：建 `trading_calendar` 表（当前 head 为 `0008`）。
- 新增 `trading-calendar` capability 规约。

**不含**：缺口检测逻辑（`detect_trading_day_gaps`）、`quality_warnings` 写入、backtest strict 模式——这些都是后续 `add-trading-day-gap-detection` change 的范围，且依赖本变更。

## Capabilities

### New Capabilities

- `trading-calendar`: 交易日历表与 akshare 同步流程，提供“哪些日子是 A 股交易日”的权威参照系，供数据完整性检查与回测守门消费。

### Modified Capabilities

（无）

## Impact

- **代码**：新增 `packages/core/src/vela_core/models/trading_calendar.py`、`packages/core/src/vela_core/trading_calendar_sync.py`；`packages/core/src/vela_core/models/__init__.py` 与 `packages/core/src/vela_core/__init__.py` 加导出；`apps/cli/src/vela_cli/main.py` 加 `sync-trading-calendar` 命令。
- **迁移**：`alembic/versions/20260709_0009_create_trading_calendar.py`（建表，非破坏）。
- **测试**：新增 `packages/core/tests/test_trading_calendar_sync.py`（同步逻辑 + 模型）与 CLI 同步命令测试。
- **依赖**：无新增（akshare 已在 `pyproject` 默认依赖）。
- **不动**：`MarketDataProvider` 契约、`market_data_fetcher`、`market_price_upsert`、计算层、`DataFetchLog`。
- **后续依赖**：`add-trading-day-gap-detection` change 将消费本变更的 `trading_calendar` 表做缺口检测（参照系来源）。
