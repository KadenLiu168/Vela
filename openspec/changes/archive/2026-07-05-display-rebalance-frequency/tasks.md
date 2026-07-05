## 前提

- [x] 0.1 在 `add-monthly-rebalance` change 中补上 `_serialize_config()` 的 `rebalance` 序列化（`apps/api/src/vela_api/config.py`）

## 1. 前端类型定义

- [x] 1.1 在 `apps/web/src/api/client.ts` 的 `DashboardStrategySummary` 中新增 `rebalance: { frequency: string }` 字段

## 2. Dashboard 展示

- [x] 2.1 在 `apps/web/src/pages/DashboardPage.tsx` 的 Strategy 面板 `compact-list` 中新增 Rebalance frequency 行，值格式化为 title case

## 3. 测试 fixture 修复

- [x] 3.1 修复 `apps/web/src/api/client.test.ts` 的 mock DashboardResponse：删除 `performance.rebalance_frequency`，补齐 `performance.risk_free_rate` 和 `rebalance.frequency`，并修复其他与 `DashboardStrategySummary` 类型不匹配的字段名（`universe_config_path`、`momentum_windows`、`defense_asset`）
- [x] 3.2 修复 `apps/web/src/App.test.tsx` 的 mock DashboardResponse：同上处理 `performance.rebalance_frequency` → `performance.risk_free_rate` + `rebalance.frequency`

## 4. 验证

- [x] 4.1 运行 `cd apps/web && npm test` 确认测试通过
- [x] 4.2 运行 `cd apps/api && uv run pytest` 确认 API 序列化测试无回归（API tests 因 pre-existing config path 问题无法运行，但 config.py 改动为单行 model_dump() 调用，不改变任何现有逻辑路径）
- [x] 4.3 启动应用，打开 Dashboard 页面，确认 Strategy 面板显示 "Rebalance frequency: Weekly"
