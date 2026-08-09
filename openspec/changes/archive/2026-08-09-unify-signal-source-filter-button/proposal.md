## Why

Signals 列表页的 SOURCE 过滤按钮（`signal-source-filter-button`）游离于 `design-system` 的三变体按钮契约之外：没有 variant className、与 `backtest-tab` 共享一套 segmented 样式（`radius-sm` 2px、`min-height: 44px`、无字体规格声明），与已统一为 `button-secondary` 的 Dashboard / Walk-forward 页面按钮视觉不一致。

## What Changes

- `SourceFilterButton`（`SignalListPage.tsx`）基座 className 增加 `button-secondary` variant，保留 `aria-pressed` 与语义类名（语义类名仅作结构/测试钩子，不再承载视觉）。
- 拆分 `styles.css` 中 `.signal-source-filter-button, .backtest-tab { ... }` 共享规则：`.backtest-tab` 保留现有 segmented 样式（tablist 语义，不在本 change 范围）；filter 按钮视觉完全由 `button-secondary` 提供。
- 新增 `.button-secondary[aria-pressed="true"]` 选中态规则：反色填充（`background: var(--color-mist)`、`color: var(--color-void)`），选择器以 `.button-` 开头，符合 "variant class is the only carrier of visual treatment"。
- filter 按钮字体规格随 `button-secondary` 统一（Inter Variable 14px / 字重 510 / `--tracking-numeral`），不再依赖浏览器默认按钮样式。

## Capabilities

### New Capabilities

（无新能力）

### Modified Capabilities

- `design-system`: "Buttons follow a three-variant contract" 与 "Buttons declare their variant via className" 增加场景——带 `aria-pressed` 的单选/过滤控件也必须携带 variant className；`button-secondary[aria-pressed="true"]` 使用反色填充作为选中态。
- `web-frontend-app`: "Signal history list page" 的 SOURCE 过滤按钮呈现契约——过滤按钮使用 `button-secondary` variant，选中段以反色填充呈现。

## Impact

- `apps/web/src/pages/SignalListPage.tsx`（`SourceFilterButton` 的 className）
- `apps/web/src/styles.css`（拆分共享规则、新增 `.button-secondary[aria-pressed="true"]`）
- `apps/web/src/pages/SignalListPage.test.tsx`（现有断言仅涉及 `aria-pressed` 与按钮名，预期不受影响；实施时评估是否补充类名断言）
- specs delta：`design-system`、`web-frontend-app`
