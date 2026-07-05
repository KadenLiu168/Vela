## 1. 对齐 detail page 所有 dl 的 dt 与 dd 字号、line-height、color

- [x] 1.1 在 `apps/web/src/styles.css` 第 758 行附近的 `.detail-page .compact-list dt` 规则中，追加 `font-size: var(--text-caption); line-height: var(--leading-caption); text-transform: uppercase; letter-spacing: 0.04em;`，使其与 1101 行 `.signal-detail-page .compact-list dt` 取值完全一致
- [x] 1.2 确认 758 行规则仍然保留 `margin-bottom: 0`（2026-07-05 字段对齐修复的产物），不被本次改动移除
- [x] 1.3 **[Fix Round 2]** 在 758 行 `.detail-page .compact-list dt` 后面新增对称的 `.detail-page .compact-list dd` 规则，覆盖 1059 行 `.detail-page dd { font-size: var(--text-body) }` 的 15px 兜底——`font-size: var(--text-caption); line-height: var(--leading-caption); color: var(--color-mist); font-weight: var(--font-weight-medium); margin: 0;`。**根因**：explore 阶段漏算了 dd 链的 specificity，1059 行的 15px 把 Backtest 的 value 强制设为 15px，与 Signal 的 13px 差 2px——这是用户浏览器复核触发的 Major finding
- [x] 1.4 **[Fix Round 3]** 扩展 1.1 + 1.3 两条规则的选择器为多选器，同时覆盖 `.detail-page .equity-curve-summary dt` 和 `.detail-page .equity-curve-summary dd`——之前 equity-curve-summary 的 dt/dd 各自回退到 `.detail-page dt/dd` 兜底（12px / 15px），跟 compact-list 不一致。**根因**：Round 1/2 只覆盖了 compact-list，没意识到 detail page 还有第二个 dl（equity-curve-summary）。**根因 2**：equity-curve-summary row gap 是 16px，compact-list 是 8px——视觉行间距不一致
- [x] 1.5 **[Fix Round 3]** `.equity-curve-summary` 基础规则的 `gap` 从 `var(--spacing-16) var(--spacing-20)` 改为 `var(--spacing-8) var(--spacing-20)`——row gap 从 16px 改到 8px，跟 compact-list 对齐

## 2. 合并"分叉式重复"CSS 规则

- [x] 2.1 删除 693 行 `.detail-page:not(.signal-detail-page) .dashboard-panel` 整段规则
- [x] 2.2 删除 722 行 `.signal-detail-page .dashboard-panel` 整段规则
- [x] 2.3 新增单条 `.detail-page .dashboard-panel` 规则，属性值取**共有属性**（B 类合并）
- [x] 2.4 删除 701 行 `.detail-page:not(.signal-detail-page) .panel-primary` 整段规则
- [x] 2.5 删除 729 行 `.signal-detail-page .panel-primary` 整段规则
- [x] 2.6 新增单条 `.detail-page .panel-primary` 规则（A 类合并：完全一致）
- [x] 2.7 **保留 751 行 `.detail-page .compact-list`，不合并**（C 类不合并）：差异大
- [x] 2.8 删除 1139 行 `.detail-page:not(.signal-detail-page) .holdings-section h3`
- [x] 2.9 删除 1145 行 `.signal-detail-page .holdings-section h3`
- [x] 2.10 新增单条 `.detail-page .holdings-section h3` 规则（D 类合并：signal margin-bottom 冗余）
- [x] 2.11 audit 合并后所有 `.detail-page .x` 新规则：与 `.dashboard-page` 不冲突
- [x] 2.12 媒体查询失效引用同步修复：3 处 dashboard-panel 双选择器合并为单条

## 3. 验证

- [x] 3.1 `cd apps/web && npm run build` 编译通过（30.00 kB css）
- [x] 3.2 `cd apps/web && npx vitest run` 测试全部通过（71 tests passed, 7 skipped）
- [ ] 3.3 **用户人工复核**（归档门禁前置条件）：浏览器打开 `/signals` 与 `/backtests`，对比：
  - `page-heading h2` 与 eyebrow 视觉一致
  - `panel-primary`（"Signal #N" / "Backtest #N"）视觉一致
  - **主 compact-list 字段 label (dt) 与 value (dd) 字号相同**（13px mist color）
  - **equity-curve-summary 字段 dt 与 dd 字号** = 13px，**行间距** = 8px，跟主 compact-list 一致 —— **本轮重点**
  - `holdings-section h3` 视觉一致
  - holdings table 表头与单元格视觉一致
  - 所有 detail 页面 dl 的 dt 与 dd 同行内 baseline 对齐
- [ ] 3.4 **用户人工复核**（归档门禁前置条件）：浏览器打开 `/`，确认 dashboard 无 `.dashboard-page` 泄漏
- [x] 3.5 `openspec validate --changes --strict` 通过
- [x] 3.6 `openspec validate --specs --strict` 通过
- [x] 3.7 `cd apps/web && npm run lint` 通过
