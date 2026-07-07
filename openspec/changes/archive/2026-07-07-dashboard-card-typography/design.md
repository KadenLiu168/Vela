## Context

Dashboard 页面 (`apps/web/src/pages/DashboardPage.tsx`, 1120 行) 单文件承载全部卡片逻辑，卡片框架在 `apps/web/src/styles.css` 中以 `.dashboard-panel` + `.dashboard-grid` 组合搭建，typography token 集中在 `apps/web/src/styles/tokens.css`。当前 typography 系统有两层约束：

1. **垂直拓展但层级不清**：`tokens.css` 已经定义了 `12 / 13 / 14 / 16 / 17 / 20 / 24 / 32 / 48 / 64 / 72 px` 的 type scale（按 `design-system` spec 强制声明），但语义角色（meta / body / emphasis / display）没有显式表达，消费者各自挑 token。
2. **Dashboard 与 Detail 双向不一致**：`detail-page-typography-consistency` spec 规定 Detail 页面两个细节页互相一致，但同时要求 Dashboard 保持"未合并前"的样式。结果就是 Dashboard 的 label 用 `--text-micro (11px)` 而 `.backtest-run-form` 用 `--text-caption (13px)`，Dashboard 的主数值 24px 与 Detail 页 `.metric-card dd` 48px 落差巨大。

本 change 在不引入新依赖、不破坏现有 `--text-body = 16px / --leading-body = 1.5` 合同的前提下，新增"卡片级 typography 阶梯"，把 Dashboard 与 Detail 的卡片视觉统一起来，并把 design-system 的 type scale 加上语义角色绑定。

## Goals / Non-Goals

**Goals:**

- 把卡片内所有视觉角色（meta / body / emphasis / display）映射到 4 档 token，token 名显式、单一来源。
- 提升 Dashboard 卡片正文可读性：13px / 1.2 → 14px / 1.5。
- 提升 Dashboard 卡片主数值视觉权重：24px → 28px，配合 `tabular-nums` 与负字距。
- 用 `--font-display` 引入一款 display 字体，仅作用于 `panel-heading h3` 与 `page-heading h1`，body / dt / dd 仍用 Inter Variable。
- 删除 `.dashboard-page .compact-list dd`、`.dashboard-page .metric span`、`.dashboard-page .panel-primary` 等"为了对抗 detail 规则泄漏"的覆盖，让所有页面共用 `.compact-list` 基础样式。
- 把 `design-system` spec 的 type scale 扩展为"卡片级 type ladder"，把同一新 value-pair 在 dashboard 与 detail 上同时生效。
- 解除 `detail-page-typography-consistency` spec 中"Dashboard 保持原样"条款，并把 Dashboard 纳入一致性范畴。

**Non-Goals:**

- 不修改后端 / API / 数据库 schema。
- 不修改移动端断点策略（仅在大于等于 768px 时启用 display 字体已足够效果）。
- 不修改 button 三变体、acid-lime 单次预留等既有 design system 合同。
- 不引入付费字体、自托管商业字体协议（EULA），仅使用 OFL / SIL / Apache-2 / MIT 协议的可商用字体。
- 不重写 Dashboard 组件结构（仍保持单文件 + 内部组件）。

## Decisions

### Decision 1：采用 4 档卡片 typography 阶梯

**方案**：在 `tokens.css` 新增以下 token（最终值在 design 阶段定稿）：

```
--card-meta-size      11px   / --leading-meta      1.4
--card-body-size      14px   / --leading-body-card 1.5
--card-emphasis-size  28px   / --leading-emphasis  1.3
--card-display-size   40px   / --leading-display-card 1.15

--tracking-meta       0.06em
--tracking-numeral   -0.01em
```

每个尺寸在 spec 中绑定到明确的视觉角色：

| 角色 | token | 字重 | 行高 | 例 |
|---|---|---|---|---|
| meta | `--card-meta-size` | 590 (semibold) | `--leading-meta` | eyebrow、status pill、compact-list dt、metric label |
| body | `--card-body-size` | 510 (medium) / 400 (input) | `--leading-body-card` | compact-list dd、metric strong 非主数值、operation summary、fetch-log meta、form input |
| emphasis | `--card-emphasis-size` | 510 (medium) | `--leading-emphasis` | panel-primary、metric strong（主数值） |
| display | `--card-display-size` | 510 (medium) | `--leading-display-card` | 详情页 `.metric-card dd` |

**理由**：
- 4 档足以覆盖 Dashboard 与 Detail 全部卡片视觉角色，token 命名遵循 `--card-*` 语义前缀，与 design-system spec 既有 `--card-bg / --card-padding-*` 一致。
- body 与 meta 之间留 3px 差（11 vs 14），保证在 mono fallback 与 letter-spacing 关闭的场景下仍能形成层级。
- emphasis 28px 替代原 24px，配合 tabular-nums 后数字（"3,000 rows"）视觉权重明显提升，与 Detail 页 48px 主数值仍保留从属关系。
- display 40px 收敛自原本的 48px，让 Detail 页主数值不至于过大。

**替代方案**：
- *保持 24px*：用户已同意升至 28px。
- *三档而非四档*：少一档会让 body 与 emphasis 跨度过大（28 vs 14 = 14px），会诱导开发者把 14-px 文字挤进 body 角色。
- *五档及以上*：增加心智负担，多数消费者没有 6 档以上需求。

### Decision 2：display 字体选型 — 优先 `Departure Mono`，fallback `IBM Plex Mono`

**方案**：引入一款带"操作面板 / 终端"美学的等宽 display 字体，作为 `panel-heading h3` 与 `page-heading h1` 的字族。

首选 **Departure Mono**（`departure-mono` 包在 `fontsource`），它是 OFL 协议，提供 `regular / medium` 两档；用作 panel-heading 可让 Dashboard 标题与 Mono 数字字段（time / error / etf-symbol）形成"控制台"调性。

若 Departure Mono 体积或加载成本过高，则 fallback 到 **IBM Plex Mono** medium（OFL，已被 JetBrains Mono 之外常见替代）。

**实施**：
- 自托管：下载 woff2 放至 `apps/web/public/fonts/`，新增 `@font-face` 规则，preload 进 `index.html`，`tokens.css` 新增 `--font-display` 命名 token，值链 `'Departure Mono', 'IBM Plex Mono', ui-monospace, monospace`（与 `--font-berkeley-mono` 同结构但不同名）。
- 不使用 `@fontsource/*` npm 包，避免新增 dependencies（design-system 决定仅依赖 OFL 自托管）。
- 不降级 Inter Variable 的 `--font-feature-settings-default`（cv01/ss03/zero/calt）。

**理由**：
- 与 JetBrains Mono 共存的"等宽控制台"调性比换 Geometric Sans（如 Inter、GT America）更显著，且不需要重新调 weight ladder。
- 公开 OFL 字体无商业风险，自托管成本可控（单文件 ~50KB）。

**替代方案**：
- *GT America / Söhne*（商用）：明确 Non-Goal。
- *Geist / Inter Tight*：与现 Inter Variable 差异较小，视觉升级有限。
- *保持 Inter Variable 加 OpenType 替代字形*（cv11、cv02）：收益小，无成本但也几乎无视觉变化。

### Decision 3：以单文件规则替换"双文件覆盖"

**方案**：
- 删除 `apps/web/src/styles.css` 中所有 `.dashboard-page .compact-list dt`、`.dashboard-page .metric span`、`.dashboard-page .panel-primary`、`.dashboard-page .compact-list dd` 等仅用于"压住 detail 规则"的覆盖。
- 在 `.compact-list`、`.metric`、`.panel-primary` 等基础规则上直接应用新 token。
- `.detail-page` 与 `.dashboard-page` 不再各自重定义这些 class 的字号 / 字重。
- `compact-list dt` 与 `compact-list dd` 在两个页面完全一致；baseline 对齐（same line-height）由 spec 保证。

**理由**：
- 未来若新增第三个页面（如 Backtest list），不需要再复制 dashboard 覆盖。
- 与 `detail-page-typography-consistency` 的目标（"两个 detail 页互相一致"）在结构上对齐。
- 减少 specificity 层级，CSS 体积预计下降约 1.5KB。

### Decision 4：form label 与 .compact-list dt 统一

**方案**：把 `.backtest-run-form label > span` 从 `13px / --leading-caption` 改为 `11px / --leading-meta / uppercase / var(--tracking-meta) / semibold`，与 `.compact-list dt` 完全一致；input 改为 `14px / regular / --leading-body-card`。

**理由**：
- form label 与 detail-list label 是同一视觉角色，分两套字会让 Operations 卡片在 Dashboard 内出现"两种 label 风格"。
- `label` 元素用 uppercase 是已有 design 模式（eyebrow、pill、status surface），不引入新概念。

### Decision 5：tabular-nums 与 mono 分配

**方案**：
- `--font-berkeley-mono` 的 `@font-face` 增加 `font-feature-settings: "tnum", "zero"`（与 body 的 `--font-feature-settings-default` 共存，name 表里 mono 优先）。
- 所有 `.metric strong`、`.panel-primary`、`.etf-row-symbol`、`.fetch-log-entry__time` 加 `font-variant-numeric: tabular-nums`。
- `.fetch-log-entry__meta`（"Fetched 120 · Inserted 119"）改为 `var(--font-berkeley-mono)` + `tabular-nums`。

**理由**：
- 数字密集处统一等宽，避免数字宽度抖动。
- 与设计意图一致：mono 在 Vela 中是"数字 / 时间 / 错误"专用，Inter 是 body 专用。

### Decision 6：panel-primary 28px 是否会撑爆 strategy-panel

**策略**：在 `.strategy-panel`（`grid-column: span 2`）渲染长 `strategy_id` 时，CSS 上加：

```
text-wrap: balance;
overflow-wrap: anywhere;
```

而不引入 `truncate` 或 clamp 行数策略——目的是保留 strategy_id 完整性。

## Risks / Trade-offs

**[Risk]** 在 Dashboard 单卡片宽度（grid 1 列下约 240–320px）下，panel-primary 从 24 → 28 可能让"3,000 rows"等短数值依然合适，但"ETF SECTOR ROTATION V1"等长 strategy_id 视觉密度变高。**Mitigation**：Decision 6 + Ladle story 提前 mock 长 strategy_id 演练。

**[Risk]** 引入 Departure Mono 后会再增加一次 LCP 阻塞（preload woff2），影响首屏。**Mitigation**：font-display 默认 swap，preload 顺序排在 InterVariable 之后；本地验证 dev network 看 LCP 是否退化（>50ms 告警）。

**[Risk]** 删除 `.dashboard-page .compact-list *` 等覆盖后，若某条 detail 规则被其他 detail 页以外使用（如 `.workflow-grid` 共用 `.compact-list`），可能发生未预期继承。**Mitigation**：在 design-system spec 中将 `.compact-list` 注册为单源契约，并写 task 强制回归 grep。

**[Risk]** 新增 token（--card-meta-size 等）与现有 `--text-caption` 等语义重叠，长期会有两个"语义不同但视觉相同"的 token 共存。**Mitigation**：在 change 内清楚列出每个新 token 与旧 token 的"consumer 重定向"，并由 design-system spec 增加"卡片级 typography 优先于 `--text-*`"指导文案。

**[Risk]** Departure Mono 与 JetBrains Mono 同时存在，可能造成"两种 mono"混淆。**Mitigation**：两者明确分工——JetBrains Mono 用于 UI 数字密集处（time / error / etf-symbol / value），Departure Mono 仅用作 panel-heading 与 page-heading 的 display 标题（仍属 mono 美学但权重不同，避免 mapping 错乱）。

## Migration Plan

**Phase 1 — Tokens（同一个 commit）**：
- `tokens.css`：新增 `--card-meta-size`/`--leading-meta`、`--card-body-size`/`--leading-body-card`、`--card-emphasis-size`/`--leading-emphasis`、`--card-display-size`/`--leading-display-card`、`--tracking-meta`、`--tracking-numeral`、`--font-display`。
- 不修改既有 token 值，避免触发 design-system spec 的 `--text-body` 条款变更。

**Phase 2 — Fonts（同一个 commit）**：
- `apps/web/public/fonts/` 引入 `DepartureMono-Regular.woff2`（必要时 `Medium`）。
- `apps/web/src/styles.css` 加 `@font-face` 规则；`index.html` 末尾追加 `<link rel="preload">`。

**Phase 3 — CSS rewrite（一个 commit 分多个文件）**：
- `styles.css`：
  - 重写 `.compact-list dt/.compact-list dd`、`.metric span/.metric strong`、`.panel-heading span`、`.panel-heading h3`、`.panel-primary`、`.status-pill`、`.dashboard-button`、`.backtest-run-form label > span/input`、`.fetch-log-entry__time/meta/error body`、`.etf-row-symbol`、`.operation-summary strong`、`.operation-link strong`。
  - 删除 `.dashboard-page .compact-list dt`、`.dashboard-page .metric span`、`.dashboard-page .compact-list dd`、`.dashboard-page .panel-primary` 等覆盖规则。
  - 为 `.dashboard-heading h1` 与 `.panel-heading h3` 增加 `font-family: var(--font-display)`。

**Phase 4 — Spec docs（一个 commit）**：
- 重新生成 `docs/tokens.md`（`npm --prefix apps/web run build:tokens-doc`）。
- 更新 `openspec/specs/design-system/spec.md`（MODIFIED Requirements）。
- 更新 `openspec/specs/detail-page-typography-consistency/spec.md`（MODIFIED + REMOVED Requirements）。

**Rollback**：
- 所有改动是 CSS / token / 字体文件级别，不修改 React 组件。回滚 = `git revert <merge-commit>`。
- 字体删除后页面会 fallback 到 monospace 系统字体，不会出现 broken layout。

## Open Questions

1. **display 字体最终选型**：Departure Mono 还是 IBM Plex Mono？需要视字体文件大小、可读性对比决定。建议在 design 阶段产出 demo HTML（用现有 panel-heading 文本）由用户拍板。
2. **是否同步修改 Dashboard 以外页面的 page-heading？** AppShell 顶部 `<h1>` 当前未设字体装饰；本 change 是否把它纳入 `--font-display`？倾向：是（同族一致性）。
3. **是否需要在 `--card-display-size` 与 `--card-emphasis-size` 上覆盖 `--tracking-heading`？** 当前 40px / 28px 没有专用字距，建议使用现有 `--tracking-heading` (-0.704px) 与新 `--tracking-numeral` (-0.01em) 即可。
