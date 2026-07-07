## Why

`npx vitest run` 在 `apps/web/` 下持续有 2 条测试失败。根因是 `App.test.tsx` 中 3 行断言在 coverage timeline UI 多次重构后未同步更新：label 文本从 `"Earliest trade date"` 变为 `"Earliest"`，且空数据状态下 timeline 不再渲染 "n/a" 占位符。

## What Changes

- 修正 `App.test.tsx` 中 3 处过时断言：
  - line 38: `getByText("Earliest trade date")` → `getByText("Earliest")`
  - line 40: `getByText("Latest trade date")` → `getByText("Latest")`
  - line 224: `getAllByText("n/a").toHaveLength(2)` → `queryAllByText("n/a").toHaveLength(0)`

## Capabilities

### New Capabilities

（无 — 纯测试断言修复）

### Modified Capabilities

- `test-suite-validation`: 前端测试套件当前有 2 条永续失败，"Frontend key component test validation" 的要求实际上未满足。修复后 `npm run test` 将稳定全量通过。

## Impact

- **测试**: `apps/web/src/App.test.tsx` — 3 行断言修正
- **无 API 改动**，**无 UI 改动**，**无业务逻辑变动**，**无依赖变更**
