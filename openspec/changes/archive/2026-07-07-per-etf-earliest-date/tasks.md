## 1. Backend — EtfBrief 扩展 & 查询修改

- [ ] 1.1 `EtfBrief` dataclass 新增 `earliest_trade_date: date | None` 字段，更新 `to_dict()` 序列化
- [ ] 1.2 `_get_market_data_status()` 中将 etf_list 查询从子查询 IN 改为 JOIN + GROUP BY，每个 ETF 附带 `func.min(MarketPrice.trade_date)`
- [ ] 1.3 运行现有测试 `test_dashboard_aggregation.py`，确认无回归

## 2. Frontend — TypeScript 类型同步

- [ ] 2.1 `client.ts` 中 `EtfBrief` 类型新增 `earliest_trade_date: string | null`
- [ ] 2.2 运行 `npm run typecheck`（或等效 TS 检查），确认类型无错误

## 3. Frontend — ETF 列表 UI 改为单列 + 日期

- [ ] 3.1 `styles.css` 中 `.etf-row-list` 的 `grid-template-columns` 从 `repeat(2, minmax(0, 1fr))` 改为 `1fr`
- [ ] 3.2 `styles.css` 中新增 `.etf-row-date` 样式：`margin-left: auto`，muted monospace 字体，`var(--color-fog)`
- [ ] 3.3 `DashboardPage.tsx` 中 `.etf-row` 渲染增加 `<span className="etf-row-date">`，显示 `etf.earliest_trade_date`（null 时显示 `—`）
- [ ] 3.4 启动 dev server 验证 UI：ETF 单列展示，日期在行尾，全局 coverage timeline 正常显示
