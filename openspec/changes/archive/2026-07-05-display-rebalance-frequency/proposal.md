## Why

后端已支持 `rebalance.frequency` 配置（weekly / monthly），但 Dashboard API 未序列化该字段，前端 Dashboard 策略面板也未展示调仓频率。用户无法从 Web UI 直接确认当前策略是按周还是按月调仓。

## What Changes

- Dashboard API (`GET /api/dashboard`) 的策略摘要中新增 `rebalance` 字段，包含 `frequency` 值
- 前端策略面板新增一行展示调仓频率，格式与现有字段一致
- 前端 API 客户端类型 `DashboardStrategySummary` 新增 `rebalance` 字段
- 清理测试 fixture 中 `performance.rebalance_frequency` 这一遗弃字段（该字段在后端类型和 API 响应中均不存在），替换为正确的 `rebalance.frequency` 和 `performance.risk_free_rate`

## Capabilities

### New Capabilities

- `web-rebalance-frequency-display`: Dashboard 策略面板展示调仓频率（Weekly / Monthly）

### Modified Capabilities

<!-- 本次改动不修改任何已有 spec 的需求。现有 web-frontend-app spec 仅覆盖 bootstrap 按钮行为，不影响。-->

## Impact

- `apps/api/src/vela_api/config.py` — `_serialize_config()` 新增 `rebalance` 字段序列化
- `apps/web/src/api/client.ts` — `DashboardStrategySummary` 类型新增 `rebalance` 字段
- `apps/web/src/pages/DashboardPage.tsx` — Strategy 面板新增 Rebalance frequency 行
- `apps/web/src/api/client.test.ts` — 修复 fixture（删 `performance.rebalance_frequency`，补 `performance.risk_free_rate` 和 `rebalance.frequency`）
- `apps/web/src/App.test.tsx` — 同上
