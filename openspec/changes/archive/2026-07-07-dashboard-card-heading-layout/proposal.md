## Why

Dashboard 卡片标题区域的视觉权重失衡：eyebrow（灰小字全大写）位于左侧，是视觉阅读的起点但权重极轻；title（大白字）位于右侧，是视觉重心却处在阅读终点。这种左右对抗的布局导致每张卡片都产生「头重脚轻」的不稳定感。

## What Changes

1. **Card heading 左右反转**：将 title（白大）移至左侧作为阅读起点，eyebrow（灰小）移至右侧作为补充分类标签
2. **Signal / Backtest / Fetches 删除 eyebrow**：这三张卡片已有 statusPill 提供辅助状态信息，无需额外分类标签
3. **内容对微调**：
   - Market: `title="Market data"` + `eyebrow="Price"`
   - Strategy: `title="Strategy"` + `eyebrow="Config"`

## Capabilities

### New Capabilities
无

### Modified Capabilities
- `web-frontend-app`: Dashboard 卡片标题布局与内容重构

## Impact

- `apps/web/src/pages/DashboardPage.tsx`: PanelHeading 调用参数调整 + eyebrow 可选化
- `apps/web/src/styles.css`: `.panel-heading` 相关布局样式调整
- `apps/web/src/App.test.tsx`: 测试查询更新
