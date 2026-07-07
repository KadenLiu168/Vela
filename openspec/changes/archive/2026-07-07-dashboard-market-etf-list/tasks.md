## 1. Python 后端 — 数据层

- [x] 1.1 在 `dashboard_aggregation.py` 中新增 `EtfBrief` dataclass（exchange / symbol / name）
- [x] 1.2 在 `DashboardMarketDataStatus` 中新增 `etf_list: tuple[EtfBrief, ...]` 字段，默认空 tuple
- [x] 1.3 更新 `DashboardMarketDataStatus.to_dict()` 序列化输出 `etf_list`
- [x] 1.4 在 `_get_market_data_status()` 中新增独立查询，JOIN `MarketPrice.etf_id` → `etf_info`，取 distinct 的 exchange / symbol / name，按 exchange + symbol 排序
- [x] 1.5 更新后端测试 `test_dashboard.py`：mock 数据中加入 `etf_list`，验证序列化

## 2. 前端 — API 类型

- [x] 2.1 在 `client.ts` 中新增 `EtfBrief` type（exchange / symbol / name）
- [x] 2.2 在 `DashboardMarketDataStatus` 中新增 `etf_list: EtfBrief[]` 字段
- [x] 2.3 更新 `client.test.ts` 中 `createDashboardResponse()` 的 mock：生成 2-3 条模拟 ETF 数据
- [x] 2.4 验证现有 dashboard mock 函数的编译和测试通过

## 3. 前端 — UI 渲染

- [x] 3.1 在 `DashboardPage.tsx` Market card 中，在 metric-row 和 compact-list 之间插入 `.etf-badge-list` 容器
- [x] 3.2 在容器内遍历 `data.market_data.etf_list`，每项渲染为 `.etf-badge`（symbol + name 两行）
- [x] 3.3 当 `etf_list` 为空时不渲染 badge 区域（保持布局完整）

## 4. 前端 — 样式

- [x] 4.1 在 `styles.css` 中新增 `.etf-badge-list`（flex-wrap、gap、margin）
- [x] 4.2 新增 `.etf-badge`（背景 / 边框 / 内边距 / border-radius）
- [x] 4.3 新增 `.etf-badge-symbol`（text-label、font-weight-medium、color-paper）
- [x] 4.4 新增 `.etf-badge-name`（text-micro、color-fog）

## 5. 前端 — 集成测试

- [x] 5.1 更新 `App.test.tsx`：在 dashboard mock 中注入 `etf_list` 数据
- [x] 5.2 添加断言：验证至少一个 ETF 的 symbol 和 name 被渲染在卡片中
- [x] 5.3 添加空列表场景：验证 `etf_list = []` 时 badge 区域不出现

## 6. 验证

- [x] 6.1 运行后端测试 `pytest apps/api/tests/test_dashboard.py`
- [x] 6.2 运行前端测试 `cd apps/web && npx vitest run`
- [x] 6.3 手动验证 dashboard 页面在浏览器中渲染正常
