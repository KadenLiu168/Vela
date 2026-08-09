# Tasks — unify-signal-source-filter-button

## 1. 组件改动

- [x] 1.1 `apps/web/src/pages/SignalListPage.tsx`：`SourceFilterButton` 的 className 由 `signal-source-filter-button` 改为 `signal-source-filter-button button-secondary`（保留 `aria-pressed` 与 `onClick`/`type="button"` 不变）

## 2. 样式改动

- [x] 2.1 `apps/web/src/styles.css`：拆分 `.signal-source-filter-button, .backtest-tab { ... }` 共享规则组——`.backtest-tab` 保留全部原声明（背景/边框/圆角/字号/min-height/focus-visible/选中态），`.signal-source-filter-button` 移除所有视觉声明
- [x] 2.2 `apps/web/src/styles.css`：拆分 `.signal-source-filter-button[aria-pressed="true"], .backtest-tab[aria-selected="true"]` 共享选中态规则——`backtest-tab` 保留原样，filter 的选中态改由 `.button-secondary[aria-pressed="true"]` 提供
- [x] 2.3 `apps/web/src/styles.css`：新增 `.button-secondary[aria-pressed="true"]` 规则（`background: var(--color-mist); color: var(--color-void); border-color: var(--color-mist)`）
- [x] 2.4 删除 filter 相关的 `.signal-source-filter-button:focus-visible` 规则（由全局 `:where(a, button, input):focus-visible` 兜底），`backtest-tab:focus-visible` 保留

## 3. 验证

- [x] 3.1 运行 `openspec validate --change unify-signal-source-filter-button --strict` 通过
- [x] 3.2 运行完整 Web gate：`npm --prefix apps/web run lint`、`lint:css`、`typecheck`、`test`、`build` 全绿
- [x] 3.3 人工确认 `/signals` 页面：过滤按钮为 secondary 描边样式，选中项为反色填充，All/Manual/Scheduled/Backtest/Legacy 交互与 `?source=` URL 同步正常
