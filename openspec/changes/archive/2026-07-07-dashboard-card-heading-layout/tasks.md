## 1. PanelHeading 组件重构

- [x] 1.1 `eyebrow` 参数改为可选（`eyebrow?: string`）
- [x] 1.2 JSX 结构反转：`<div class="panel-heading-start">` 内含 `<h3>{title}</h3>` + statusPill，放在左侧；`<span>{eyebrow}</span>` 放在右侧，eyebrow 为空时不渲染

## 2. CSS 布局调整

- [x] 2.1 新增 `.panel-heading-start` 样式（复制 `.panel-heading-end`，`justify-content` 改为 `flex-start`）
- [x] 2.2 删除 `.panel-heading-end` 样式（废弃）
- [x] 2.3 确认 `.panel-heading` 的 `space-between` 在反转后仍正常工作

## 3. 卡片标题对内容更新

- [x] 3.1 Market card: `eyebrow="Market" title="Price data"` → `eyebrow="Price" title="Market data"`
- [x] 3.2 Strategy card: `eyebrow="Strategy" title="Parameters"` → `eyebrow="Config" title="Strategy"`
- [x] 3.3 Signal card: `eyebrow="Signal" title="Latest result"` → 删除 eyebrow，`title="Latest signal"`
- [x] 3.4 Backtest card: `eyebrow="Backtest" title="Latest result"` → 删除 eyebrow，`title="Latest backtest"`
- [x] 3.5 Fetches card: `eyebrow="History" title="Fetches"` → 删除 eyebrow，`title="Data fetches"`

## 4. 测试同步

- [x] 4.1 更新 Market panel 测试查询（`"Price data"` → `"Market data"`）
- [x] 4.2 更新 Strategy panel 测试查询（`"Parameters"` → `"Strategy"`）
- [x] 4.3 更新 Fetches panel 测试查询（`"Fetches"` → `"Data fetches"`）
