## Why

当前 Market Data 卡片只展示全局的 earliest/latest trade date，无法知道每只 ETF 各自的数据从哪天开始。做回测选时间时，如果选了一个某些 ETF 还没数据的日期，策略信号会异常。同时 ETF 列表用 2-column grid，信息密度低，加日期后一行放不下。

## What Changes

- 后端 dashboard aggregation 的 `_get_market_data_status()` 改为按 `etf_id` GROUP BY，计算每只 ETF 的 `MIN(trade_date)`，合并到已有的 `etf_list` 查询中
- `EtfBrief` dataclass 新增 `earliest_trade_date: date | None` 字段
- 前端 `EtfBrief` TypeScript 类型新增 `earliest_trade_date: string | null`
- ETF 列表从 2-column grid 改为单列（`grid-template-columns: 1fr`），每行右侧显示最早数据日期
- 全局 coverage timeline 保持不变 — 它仍然是所有 ETF 的并集范围，提供总览

## Capabilities

### New Capabilities

（无 — 本次改动均在已有能力范围内扩展）

### Modified Capabilities

- `dashboard-aggregation`: `EtfBrief` 新增 `earliest_trade_date` 字段；聚合查询增加 GROUP BY 以计算每只 ETF 的最早 trade_date
- `market-data-etf-visibility`: API 响应中每个 ETF 条目新增 `earliest_trade_date`；ETF 列表从 2-column grid 改为单列，每行展示最早日期
- `web-frontend-app`: Market data card 的 ETF list 场景从 flat 2-column grid 改为 flat 1-column list with date

## Impact

- **Backend**: `dashboard_aggregation.py` — `EtfBrief` dataclass、`_get_market_data_status()` 查询、`to_dict()`
- **API types**: `EtfBrief` 序列化增加 `earliest_trade_date` 字段（ISO date string or null）
- **Frontend types**: `client.ts` 中 `EtfBrief` 增加 `earliest_trade_date: string | null`
- **Frontend UI**: `DashboardPage.tsx` ETF 行渲染增加日期显示；`styles.css` `.etf-row-list` grid 改为单列
- **无 breaking change** — 全局 `earliest_trade_date`/`latest_trade_date` 不变，coverage timeline 不变，`etf_list` 保持相同的排序和过滤逻辑
