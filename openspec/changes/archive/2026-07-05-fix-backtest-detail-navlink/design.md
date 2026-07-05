## Context

导航栏的 "Backtest Detail" 按钮硬编码为 `/backtests/1`。用户运行多次回测后，点击该按钮始终回到 Backtest #1（最早的一次），而非最近一次。Dashboard 面板中的 "View backtest detail" 链接已正确使用动态 run_id。

现有路由结构：

```
/                  → DashboardPage
/signals/:id       → SignalDetailPage
/backtests/:id     → BacktestDetailPage  (当前只匹配此模式)
```

当前 `BacktestDetailPage` 要求 `backtestId` 为必选参数。

## Goals / Non-Goals

**Goals:**
- 点击导航栏的 "Backtest Detail" 时自动展示最近一次回测
- 保留通过 `/backtests/{id}` 访问特定回测详情的功能
- 改动最小化，不引入新页面

**Non-Goals:**
- 不创建回测历史列表页（可在后续变更中实现）
- 不修改后端 API
- 不修改 Dashboard 面板中已有的动态链接

## Decisions

### 1. 使用 `/backtests`（无 ID）作为导航链接

之前是 `/backtests/1`（硬编码 ID）。改为不带 ID 的路径，语义更清晰。

### 2. 在 `BacktestDetailPage` 中支持可选 ID

当前 `backtestId` 是必选参数。改为可选：当有 ID 时获取指定回测，无 ID 时调用 `/api/backtests?limit=1` 获取最新一条。

使用现成的 `list_backtests` API（`GET /api/backtests?limit=1`），无需新增后端接口。

### 3. 路由匹配顺序

`/backtests/:id` 和 `/backtests` 两条路由。在 `App.tsx` 中：
- 先精确匹配 `/backtests` → 无 ID
- 再正则匹配 `/backtests/:id` → 有 ID

### 4. 状态管理

现有 `BacktestDetailState` 的 `backtestId` 字段改为可选。新增状态：当无 ID 且 API 返回空列表时显示 "No backtest runs yet" 空状态。

## Risks / Trade-offs

- **导航栏切换到 `/backtests` 后 URL 不变**：用户停留在 `/backtests` 页面时，如果刷新或分享该 URL，会看到最新回测。这不是问题，对于未指定 ID 的入口这是正确行为。
- **不向后兼容**：旧的书签收藏的 `/backtests/1` 仍然有效，不会破坏。
