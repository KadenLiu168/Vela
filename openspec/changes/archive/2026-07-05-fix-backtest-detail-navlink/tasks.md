## 1. 导航链接和路由修改

- [x] 1.1 修改 `App.tsx`：将导航栏 "Backtest Detail" 的 `href` 从 `/backtests/1` 改为 `/backtests`
- [x] 1.2 修改 `App.tsx` 的 `renderRoute` 函数：增加 `/backtests` 的精确匹配，传入 `undefined` 作为 `backtestId`

## 2. BacktestDetailPage 支持无 ID 自动加载最新回测

- [x] 2.1 修改 `BacktestDetailPage` 的 Props 类型：将 `backtestId` 改为可选（`backtestId?: string`）
- [x] 2.2 在 `BacktestDetailPage` 中添加副作用：当 `backtestId` 为空时，调用 `/api/backtests?limit=1` 获取最近回测并自动加载
- [x] 2.3 更新 `BacktestDetailState` 类型：`backtestId` 改为可选（`backtestId?: string`）
- [x] 2.4 处理空状态：当 API 返回空列表时显示 "No backtest runs yet" 提示
- [x] 2.5 必要时更新测试文件以覆盖新增的无 ID 路径

## 3. 验证

- [x] 3.1 确认点击导航栏 "Backtest Detail" 时 URL 变为 `/backtests` 并加载最新回测
- [x] 3.2 确认通过 `/backtests/{id}` 访问指定回测详情仍然正常
- [x] 3.3 确认无回测数据时显示空状态提示
- [x] 3.4 确认 Dashboard 面板的 "View backtest detail" 链接不受影响
