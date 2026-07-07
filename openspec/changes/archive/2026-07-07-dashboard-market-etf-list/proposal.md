## Why

Market Data 卡片当前只显示"Covered ETFs: 9 ETFs"这样的数字统计，用户无法直观看到具体有哪些 ETF 已有行情数据。在查看 dashboard 时，用户需要快速确认数据覆盖了哪些标的，而不是翻到配置页去核对。这个信息缺口让 dashboard 的实际诊断价值打了折扣。

## What Changes

- **Dashboard API 响应扩展**：`DashboardMarketDataStatus` 新增 `etf_list` 字段，返回已有行情数据的 ETF 列表（exchange、symbol、name），类型为数组
- **后端 QUERY 增强**：`_get_market_data_status()` 新增 JOIN `etf_info` 查询，筛选出 `MarketPrice` 中有记录的唯一 ETF
- **前端 Market Data 卡片展示**：在 statistics（price rows / covered ETFs）下方、日期区间上方，以 badge 形式展示每条 ETF 记录（`symbol · name`）
- **Badge 样式**：参照设计系统的 `--surface-carbon`、`--color-fog` 等 token，新增 `.etf-badge` 样式集
- **Mock 与测试更新**：所有涉及 dashboard mock 数据的地方同步扩展 `etf_list` 字段

## Capabilities

### New Capabilities
- `market-data-etf-visibility`: dashboard Market Data 卡片中展示有行情数据的 ETF 列表

### Modified Capabilities
- 无（本次不修改已有 spec 的 req 变更）

## Impact

- `packages/core/src/vela_core/dashboard_aggregation.py`：`DashboardMarketDataStatus` dataclass 和 `to_dict()` 方法新增 `etf_list` 字段；`_get_market_data_status()` 新增 JOIN 查询
- `apps/api/src/vela_api/main.py`：dashboard 端点需把 ETF pool 信息传递给 `get_dashboard_summary()`
- `apps/web/src/api/client.ts`：`DashboardMarketDataStatus` TypeScript 类型新增 `etf_list`
- `apps/web/src/pages/DashboardPage.tsx`：Market card 中渲染 ETF badge 列表
- `apps/web/src/styles.css`：新增 `.etf-badge` 相关样式
- 两端的测试文件同步更新 mock 数据
