## 1. 后端 — EtfBrief 新增 category 字段

- [x] 1.1 在 `dashboard_aggregation.py` 中 `EtfBrief` 新增 `category: str` 字段
- [x] 1.2 在 `_get_market_data_status()` 的 JOIN 查询中加入 `ETFInfo.category`
- [x] 1.3 更新 `test_dashboard.py` 中 `etf_list` mock 数据，加入 `category`
- [x] 1.4 更新 `test_api_contract.py` / `test_market_data_fetch.py` 中 `etf_list` mock，加入 `category`

## 2. 前端 API 类型

- [x] 2.1 在 `client.ts` 中 `EtfBrief` 新增 `category: string`
- [x] 2.2 更新 `client.test.ts` 中 `market_data.etf_list` mock 加入 `category`

## 3. CSS — 替换 badge 样式为行列表样式

- [x] 3.1 移除 `.etf-badge-list`、`.etf-badge`、`.etf-badge-symbol`、`.etf-badge-name` 四组样式
- [x] 3.2 新增 `.etf-row-list`（margin 控制间距）
- [x] 3.3 新增 `.etf-row`（flex row、border-top、hover transition、:first-child）
- [x] 3.4 新增 `.etf-row-bar`（3px 宽色条）
- [x] 3.5 新增 `.etf-row-symbol`（mono font、paper color）
- [x] 3.6 新增 `.etf-row-dot`（smoke color 分隔点）
- [x] 3.7 新增 `.etf-row-name`（fog color、ellipsis overflow）

## 4. React — 替换 JSX 结构

- [x] 4.1 在 `DashboardPage.tsx` 中添加 `barColor()` 内联函数（category → CSS var）
- [x] 4.2 将 `.etf-badge-list` → `.etf-row-list`，内部结构改为 `.etf-row > .etf-row-bar + .etf-row-symbol + .etf-row-dot + .etf-row-name`
- [x] 4.3 验证空列表条件渲染逻辑不变

## 5. 测试

- [x] 5.1 更新 `App.test.tsx` 中 mock `etf_list` 加入 `category`
- [x] 5.2 确认 `market.getByText("SPY")` / `market.getByText("SPY ETF")` 等断言在新 DOM 下通过
- [x] 5.3 确认空列表场景 `screen.queryByText("SPY")` 仍通过

## 6. 验证

- [x] 6.1 运行后端测试 `pytest apps/api/tests/test_dashboard.py test_api_contract.py test_market_data_fetch.py`
- [x] 6.2 运行前端测试 `cd apps/web && npx vitest run`
- [x] 6.3 运行 TypeScript 类型检查 `cd apps/web && npx tsc --noEmit`
- [x] 6.4 手动验证浏览器渲染效果
