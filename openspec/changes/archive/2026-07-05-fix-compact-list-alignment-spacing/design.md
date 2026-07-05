## Context

当前 `compact-list` 是一个 CSS Grid 定义列表（`grid-template-columns: max-content minmax(0, 1fr)`），在 Dashboard、Backtest Detail、Signal Detail 三个页面中复用。每个页面通过作用域选择器（`.dashboard-page .compact-list` 等）进行微调。

现有的 CSS 层级：

```
.compact-list                        → 基础（line 739）
.dashboard-page .compact-list        → Dashboard 覆盖（line 746）
.detail-page .compact-list           → Backtest Detail 覆盖（line 751）
.signal-detail-page .compact-list    → Signal Detail 覆盖（line 1092）
```

两个问题源于 `.compact-list` 缺少两个关键属性：
- 无 `align-items` → 默认 `stretch`，不同字号的 dt（11px）/dd（13px）文字基线不齐
- 行间距 `gap` 仅 8px（signal-detail 为 12px）→ 值文字 13px，行间拥挤

影响范围：修改仅涉及 `apps/web/src/styles.css`，不改动任何 TSX 组件。

## Goals / Non-Goals

**Goals:**
- 同行 dt/dd 文字基线对齐（`align-items: baseline`）
- 行间距从 8px/12px 统一增加到 16px
- 列间距保持不变（Dashboard/Backtest Detail: 16px, Signal Detail: 20px）
- 移动端（≤720px 单列布局）不受影响

**Non-Goals:**
- 不重构 HTML 结构或组件
- 不修改 font-size、color 等样式
- 不提取共享 Detail 组件（超出本次范围）
- 不合并冗余的作用域 CSS 规则

## Decisions

### Decision 1: 在基础规则而非各作用域变体中添加 `align-items`

**选择**：仅在 `.compact-list` 基础规则（line 739）中添加 `align-items: baseline`。

**理由**：所有三个作用域变体都不覆盖 `align-items`，基础规则的新属性会自动级联。无需 4 处重复。

**备选**：在每个作用域变体中各加一次 — 冗余，增加维护负担。

### Decision 2: 行间距统一为 16px

**选择**：将所有作用域的 row-gap 统一为 `var(--spacing-16)`（16px）。

**理由**：
- 当前 8px 过紧：13px 值的底部距下一行 11px 标签的顶部仅 8px，视觉上拥挤
- Signal Detail 已是 12px，仍偏紧
- 16px 约为值文字（13px）的 1.2 倍，比例舒适
- 不选择 20px：对于快速扫读的定义列表，20px 间隔过大，会让内容显得松散

**备选**：12px — 改善不明显，仍可能感觉拥挤；20px — 过大，列表纵向过长。

### Decision 3: 每个作用域分别修改 gap 值（不依赖级联）

**选择**：在每个 `.xxx-page .compact-list` 规则中独立修改 gap 值，共 4 处。

**理由**：每个作用域都显式声明了 `gap`，会覆盖基础规则。不修改它们则基础规则的 gap 不生效。理想的后续重构是移除这些冗余声明，但本次遵循「最小改动」原则。

## Risks / Trade-offs

- [Risk] 16px 行间距在数据密集页面（如 Dashboard 多个 compact-list 面板）可能让面板变高 → 每个 compact-list 通常 5-7 行，增加高度约 40-48px，在现有面板 padding 内可接受
- [Risk] `align-items: baseline` 在移动端单列模式下无实际作用，但也不产生副作用 → 低风险
