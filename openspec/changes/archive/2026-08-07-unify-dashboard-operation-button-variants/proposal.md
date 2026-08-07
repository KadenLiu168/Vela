## Why

Dashboard Operations 面板的 `operation-list`（`DashboardPage.tsx:380-416`）中，"Fetch full" 按钮使用 `button-tertiary`（text-only：无边框、左右 padding 8px），而同一按钮组内的 "Fetch market data"、"Generate signal"、"Run backtest" 均使用 `button-secondary`（描边、padding 20px），另有主操作使用 `button-primary`。同一行内三种视觉重量混排，使 "Fetch full" 看起来像"缺了样式"，与用户预期的按钮一致性不符。

## What Changes

- 将 `DashboardPage.tsx` 中 "Fetch full" 按钮的 `className` 从 `button-tertiary` 改为 `button-secondary`，与同组其他常规操作按钮一致。
- 保留按钮的 `title="Re-downloads all ETF price history"` 与文案 "Fetch full"，次要性由文案与提示表达，不再依赖弱化样式。
- 同步 `design-system` spec：在 "Buttons follow a three-variant contract" 下补充"同一操作组内按钮使用一致档位"的场景，防止再次混排。

## Capabilities

### New Capabilities

（无新能力引入。）

### Modified Capabilities

- `design-system`: "Buttons follow a three-variant contract" 需求补充场景——同一操作组（`.operation-list`）内的按钮 MUST 使用相同的视觉档位（`secondary`），仅视图级主操作可使用 `primary`，避免 text-only 与 outline 变体在同一按钮组内混排。

## Impact

- `apps/web/src/pages/DashboardPage.tsx`：第 390 行 "Fetch full" 按钮类名。
- `apps/web/src/styles.css`：`button-tertiary` 规则保留（仍为合法三档之一，供其他场景使用），无 CSS 改动。
- 测试：`DashboardPage.test.tsx` 若断言按钮类名需同步；运行完整 Web gate 验证。
- 文档：`openspec/specs/design-system/spec.md` 同步更新。
