## Why

`WalkForwardListPage.tsx` 的 "Run walk-forward" 按钮使用 `className="action-button"`（第 155 行），外层容器 `walk-forward-run-trigger`（第 153 行）也无任何样式。`action-button` 不是 `design-system` 三档按钮契约（`button-primary` / `button-secondary` / `button-tertiary`）中的合法类名，`styles.css` 中不存在对应规则——按钮渲染为浏览器默认样式，与全站按钮体系不一致，且违反既有 spec "Buttons declare their variant via className"。

## What Changes

- 将 `apps/web/src/pages/WalkForwardListPage.tsx` 中 "Run walk-forward" 按钮的 `className` 从 `action-button` 改为 `button-secondary`（与 Dashboard operations 中的常规操作按钮同档）。
- 在 `apps/web/src/styles.css` 新增 `.walk-forward-run-trigger` 规则，为 run-trigger 容器提供与 Signals 页 filter（`margin-bottom: var(--spacing-16)`）一致的底部间距，使按钮与下方表格的间距与列表页惯例对齐。
- 更新 `web-frontend-app` spec 的 "Walk-forward list page provides run trigger" 需求，显式约束 run-trigger 按钮的呈现（使用合法按钮变体类名）。

## Capabilities

### New Capabilities

（无新能力引入。）

### Modified Capabilities

- `web-frontend-app`: "Walk-forward list page provides run trigger" 需求补充呈现约束场景——run-trigger 按钮 MUST 使用 `design-system` 三档变体类名之一（`button-secondary`），不得携带未在 `styles.css` 中定义的样式类名。

## Impact

- `apps/web/src/pages/WalkForwardListPage.tsx`：run-trigger 按钮类名。
- `apps/web/src/styles.css`：新增 `.walk-forward-run-trigger` 间距规则。
- 测试：`WalkForwardListPage.test.tsx` 若断言按钮类名需同步；运行完整 Web gate 验证。
- 文档：`openspec/specs/web-frontend-app/spec.md` 同步更新。
