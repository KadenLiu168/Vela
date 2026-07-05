## Why

Dashboard、Signal Detail、Backtest Detail 三个页面的 `compact-list`（label-value 定义列表）存在两个视觉问题：1) 标签（11px）与对应值（13px）字体大小不一致，因缺少 `align-items: baseline`，同行内的文字基线未对齐；2) 行间距仅 8px，值文字较大导致行与行之间显得拥挤。问题覆盖全部三个页面。

## What Changes

- 为 `.compact-list` 基础规则添加 `align-items: baseline`，使同行 dt/dd 文字基线对齐（自动级联到所有页面作用域变体）
- 将 `.compact-list`、`.dashboard-page .compact-list`、`.detail-page .compact-list` 的行间距从 `--spacing-8`（8px）增至 `--spacing-16`（16px）
- 将 `.signal-detail-page .compact-list` 的行间距从 `--spacing-12`（12px）增至 `--spacing-16`（16px）
- 列间距保持不变

## Capabilities

### New Capabilities

无新增能力。

### Modified Capabilities

- `web-frontend-app`: 添加 compact-list 文字基线对齐与行间距要求，确保 label-value 定义列表在所有页面中的视觉整洁度。

## Impact

- `apps/web/src/styles.css` — 4 处 CSS 规则块内的 5 行修改（gap 行间距值 + align-items 属性）
