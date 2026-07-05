## Context

Backtest Detail 页面的 `compact-list`（`<dl>`）同时匹配以下 CSS 规则：

| 选择器 | 行号 | 关键属性 |
|--------|------|----------|
| `.compact-list` | 739 | `gap: 8px 16px`, `grid-template-columns: max-content minmax(0, 1fr)` |
| `.detail-page dl` | 1072 | `gap: 16px`, `padding: 20px`, `margin: 24px 0 0` |
| `.detail-page dt` | 1048 | `margin-bottom: 8px`, `font-size: --text-label (12px)`, `text-transform: uppercase` |

由于 `.detail-page dl/dt/dd` 的 specificity (0,0,1,1) 高于 `.compact-list` (0,0,1,0)，通用规则覆盖了 `.compact-list` 的设置，导致：
- 行间距变为 16px（预期 8px）
- `<dt>` 底部多出 8px margin，与其同行的 `<dd>` 没有，破坏垂直对齐
- dt 字号 12px (uppercase) vs dd 字号 13px (normal)，视觉基线不一致

Signal Detail 页面通过独立的 `.signal-detail-page .compact-list` 规则避免了此问题。

## Goals / Non-Goals

**Goals:**
- Backtest Detail 页面的字段标签和值在每行内垂直对齐
- 行间距恢复到合理值（与 Signal Detail page 一致）
- 保持现有的视觉风格（颜色、边框、字体）

**Non-Goals:**
- 不改变 Signal Detail 或 Dashboard 页面的布局
- 不修改 HTML 结构
- 不改动全局 `.compact-list` 样式

## Decisions

### 1. 添加 `.detail-page .compact-list` 专用规则

遵循 Signal Detail 页面的模式（`.signal-detail-page .compact-list`），为 Backtest Detail 页面添加 scope 化的规则。通过明确设置所有被覆盖的属性来阻止级联溢出。

### 2. 具体覆盖值

```css
.detail-page .compact-list {
  gap: var(--spacing-8) var(--spacing-16);  /* 行 8px，列 16px */
  margin: var(--spacing-16) 0 0;
  padding: var(--spacing-16);
  /* grid-template-columns 继承自 .compact-list，无需重复 */
}
```

之所以选择这些值：
- `gap: 8px 16px` — 与 `.compact-list` 预期一致，覆盖 `.detail-page dl` 的 `gap: 16px`
- `margin: 16px 0 0` — 与 `.compact-list` 预期一致
- `padding: 16px` — 替代 `.detail-page dl` 的 `20px`，与 Signal Detail 页面的 `padding: var(--spacing-16)` 保持一致
- `background`, `border`, `border-radius` 从 `.detail-page dl` 继承（保留卡片样式）

### 3. 不移除 `.detail-page dt` 的 margin-bottom

`margin-bottom: 8px` 是从 `.detail-page dt` 继承的，它影响所有 detail 页面的 dt。考虑到移除它可能影响其他页面，只通过作用域化的 `.detail-page .compact-list dt` 重置它。

## Risks / Trade-offs

- **专有规则增加 CSS 体积**：一行专用规则，影响极小
- **与 Signal Detail 页面值不一致**：Signal 使用 `gap: 12px 20px`，Backtest 使用 `gap: 8px 16px`。这是合理差异——Signal 页面数据量少，可以有更宽松的间距
