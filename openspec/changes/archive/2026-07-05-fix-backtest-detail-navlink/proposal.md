## Why

导航栏的"Backtest Detail"链接硬编码为 `/backtests/1`，始终指向 Backtest #1。用户多次运行回测后，点击导航进入详情页时永远看到的是最早的一次回测，而非最近的一次，与用户预期不符。其他入口（Dashboard 面板的 "View backtest detail"）已正确链接到对应回测，只有导航栏的入口存在此问题。

## What Changes

- 将导航栏 `navItems` 中的 "Backtest Detail" 链接从 `/backtests/1` 改为 `/backtests`（不带 ID）
- 在 `App.tsx` 中添加 `/backtests` 的精确匹配路由
- 在 `BacktestDetailPage` 中增加对 `backtestId` 为空的处理：当无 ID 时自动从 API 获取最近一次回测并展示
- `getActivePath` 中 `/backtests/` 前缀匹配逻辑保留，无需修改

所有改动仅限于 Web 前端路由和组件层。

## Capabilities

### New Capabilities

无新增能力。

### Modified Capabilities

无现有能力需求变更。

## Impact

- `apps/web/src/App.tsx` — 修改导航栏链接和路由匹配
- `apps/web/src/pages/BacktestDetailPage.tsx` — 支持无 ID 时自动加载最新回测
