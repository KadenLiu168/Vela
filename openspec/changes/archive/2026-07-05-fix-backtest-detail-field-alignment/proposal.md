## Why

Backtest Detail 页面的字段（label）和对应值（value）在垂直方向上没有对齐。原因是通用样式 `.detail-page dl` / `.detail-page dt` 的 specificity 高于 `.compact-list`，覆盖了正确的网格间距和内边距值，导致行间距过大且行列元素不齐。

此问题影响 Backtest Detail 页面的数据可读性和视觉整洁度，与 Signal Detail 页面已正确处理的对齐效果不一致。

## What Changes

- 为 Backtest Detail 页面的 `.compact-list` 添加作用域下的专用样式规则，与 Signal Detail 页面的处理模式保持一致
- 明确设置 `grid-template-columns`、`gap`（行列间距）、`margin`、`padding`，不被通用 `.detail-page dl/dt/dd` 规则覆盖
- 移除 `dt` 上不必要的 `margin-bottom`，确保同行标签和值垂直对齐

## Capabilities

### New Capabilities

无新增能力。

### Modified Capabilities

无现有能力需求变更。

## Impact

- `apps/web/src/styles.css` — 添加 `.detail-page .compact-list` 专用规则，覆盖 `.detail-page dl` 的冲突属性
