## 1. CSS 修改

- [ ] 1.1 `.compact-list` 基础规则（line 741）：行间距 `--spacing-8` → `--spacing-16`
- [ ] 1.2 `.compact-list` 基础规则（line 744）：新增 `align-items: baseline;`
- [ ] 1.3 `.dashboard-page .compact-list`（line 747）：行间距 `--spacing-8` → `--spacing-16`
- [ ] 1.4 `.detail-page .compact-list`（line 752）：行间距 `--spacing-8` → `--spacing-16`
- [ ] 1.5 `.signal-detail-page .compact-list`（line 1094）：行间距 `--spacing-12` → `--spacing-16`

## 2. 验证

- [ ] 2.1 `cd apps/web && npm run build` — 确认构建无错
- [ ] 2.2 打开 Dashboard (`/`) — 确认 Strategy/Market 卡片中 label-value 基线对齐、行间距舒适
- [ ] 2.3 打开 Backtest Detail (`/backtests`) — 确认 backtest info 区域对齐与间距
- [ ] 2.4 打开 Latest Signal (`/signals/demo-signal`) — 确认 signal info 区域对齐与间距
- [ ] 2.5 窗口调整到 ≤720px — 确认单列布局无异常
- [ ] 2.6 `cd apps/web && npx vitest run` — 确认现有测试通过
