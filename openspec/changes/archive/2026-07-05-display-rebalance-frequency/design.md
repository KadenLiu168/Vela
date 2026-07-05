## Context

`add-monthly-rebalance` 在 `packages/core/` 中新增了 `RebalanceConfig`（`frequency: "weekly" | "monthly"`），但 `apps/api/src/vela_api/config.py` 的 `_serialize_config()` 漏掉了 `rebalance` 字段的序列化。因此前端 Dashboard 无法获取调仓频率。

本次改动分两步：
1. 在归档的 `add-monthly-rebalance` change 中补上 API 序列化（一行代码）
2. 新建 `display-rebalance-frequency` change 完成前端展示

## Goals / Non-Goals

**Goals:**
- Dashboard Strategy 面板展示调仓频率（Weekly / Monthly），格式跟随现有 `compact-list` 风格
- `GET /api/dashboard` 响应的 strategy 段新增 `rebalance: { frequency: "weekly" | "monthly" }`
- 清理测试 fixture 中的遗弃字段 `performance.rebalance_frequency`

**Non-Goals:**
- SignalDetail / BacktestDetail 不展示调仓频率
- 不改动 `PerformanceConfig` 类型
- 不引入其他频率（biweekly 等）

## Decisions

### Decision 1: API 响应结构 — 嵌套 `rebalance` 对象

```json
{
  "strategy": {
    "rebalance": { "frequency": "weekly" }
  }
}
```

**Rationale:** 与后端 `StrategyConfig` 的嵌套结构一致（`config.strategy.rebalance.model_dump()`），也和现有 `momentum`、`score_weights` 等子段风格统一。不扁平化为 `rebalance_frequency: "weekly"`。

### Decision 2: 前端类型 — 显式字面量 vs Record

```typescript
rebalance: { frequency: string };
```

**Rationale:** 目前只展示不操作，`string` 足够。日后如果需要枚举约束可以用 `"weekly" | "monthly"`，但当前不需要。

### Decision 3: 显示格式 — title case

API 值 `"weekly"` → 展示 `"Weekly"`，`"monthly"` → `"Monthly"`。

**Rationale:** 与现有信息密度一致，直接在 JSX 中处理（`value.charAt(0).toUpperCase() + value.slice(1)`），不需要新增 formatter 函数。

### Decision 4: 测试 fixture — 删而不是兼容

两个 fixture (`client.test.ts:204`, `App.test.tsx:1727`) 中的 `performance: { rebalance_frequency: "weekly" }` 直接删除，替换为：
- `performance: { risk_free_rate: 0.02 }`（API 实际返回的字段）
- `rebalance: { frequency: "weekly" }`（新增字段）

**Rationale:** `performance.rebalance_frequency` 从来不是 API 的真实字段。保留它或为其添加类型兼容会固化错误的 API 契约。

## Risks / Trade-offs

- [Risk] `client.test.ts` 的 fixture 不仅 `performance` 有误，其他字段名也有多处与 `DashboardStrategySummary` 类型不匹配（如 `universe_config_path` → `universe_config`、`momentum_windows` → `momentum`、`defense_asset` → `defense`）。→ **本次一并修复**，使 fixture 与类型定义对齐。

## Open Questions

- 无。API 序列化对齐在 `add-monthly-rebalance` change 中完成，本次只关注前端展示。
