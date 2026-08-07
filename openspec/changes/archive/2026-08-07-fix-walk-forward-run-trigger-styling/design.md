## Context

`WalkForwardListPage.tsx:153-176` 渲染 run-trigger 区域：

```tsx
<div className="walk-forward-run-trigger">
  <button className="action-button" ...>Run walk-forward</button>
  ...
</div>
```

问题：

- `action-button` 在 `styles.css`（2123 行，全站唯一样式文件）中无任何定义 → 按钮为浏览器默认样式，无圆角、无 hover/disabled 视觉反馈。
- `walk-forward-run-trigger` 同样无定义 → 按钮与下方表格之间无间距，与 Signals 页 filter（`.signal-source-filter`，`margin-bottom: var(--spacing-16)`）不一致。
- 违反 `design-system` spec "Buttons declare their variant via className"：每个 `<button>` 必须携带 `button-primary` / `button-secondary` / `button-tertiary` 三档之一。

`design-system` spec 已定义完整三档按钮体系（styles.css:1174-1239），无需新增视觉规则。

## Goals / Non-Goals

**Goals:**

- run-trigger 按钮改用合法变体 `button-secondary`，获得与全站一致的圆角、hover、disabled 视觉。
- run-trigger 容器间距与列表页惯例对齐（`margin-bottom: var(--spacing-16)`）。
- 同步 `web-frontend-app` spec，使 run-trigger 的呈现约束可测。

**Non-Goals:**

- 不重构按钮体系（属于独立的 `extract-shared-button-component` change）。
- 不改动 run-trigger 的行为逻辑（轮询、导航、错误处理）。
- 不调整其他页面。

## Decisions

### 决策 1：run-trigger 按钮使用 `button-secondary`

- 备选：`button-primary`（更突出）或 `button-tertiary`（更弱化）。
- 选择理由：run-trigger 是列表页的常规操作（非每视图唯一的 CTA，与 Dashboard 的 Bootstrap 主操作不同），`secondary` 与 Signals 页 filter 之后的页面操作语言一致；`design-system` spec 的 "Acid-lime is reserved for the per-view primary CTA" 也提示 primary 应留给视图级唯一主操作，不应被 run-trigger 占用。

### 决策 2：新增 `.walk-forward-run-trigger { margin-bottom: var(--spacing-16); }`

- 备选：复用 `.signal-source-filter` 的类名（语义不符）或加 flex 容器类。
- 选择理由：run-trigger 是唯一需要间距的容器，一条最小规则即可；`--spacing-16` 与 Signals 页 filter 的 `margin-bottom` 一致，保证列表页内容间距统一。

### 决策 3：spec 采用 MODIFIED `web-frontend-app`

- 备选：MODIFIED `design-system`。
- 选择理由：run-trigger 按钮的呈现约束是页面行为需求的一部分，`web-frontend-app` 的 "Walk-forward list page provides run trigger" 正是该功能的权威描述位置；`design-system` 已规定通用按钮契约，无需重复。

## Risks / Trade-offs

- 按钮从无样式变为 `secondary` 描边样式，视觉变化明显但方向正确 → 由测试与截图确认。
- 若测试断言旧的 `action-button` 类名，需同步更新 → 运行 `WalkForwardListPage.test.tsx` 定位。
- `.walk-forward-run-trigger` 间距规则与后续 P2 组件化（Button 组件）不冲突，P2 只封装按钮本身，容器间距留在页面层。

## Migration Plan

- 纯前端 CSS/TSX 改动，无数据库/接口迁移。
- 回滚：`git revert` 类名与 CSS 规则两处改动即可，独立无副作用。
