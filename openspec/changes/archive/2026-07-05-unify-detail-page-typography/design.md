## Context

Vela web 前端的两个 detail 页面 (`/signals/:id?` 与 `/backtests/:id?`) 共享 `.page.detail-page` 外壳与 `dashboard-panel` / `compact-list` / `holdings-section` 等内部结构组件。Signal 与 Backtest 详情由两个独立 React 组件实现（`apps/web/src/pages/SignalDetailPage.tsx` 与 `BacktestDetailPage.tsx`），HTML 树高度对称：每个页面都有 `page-heading`（h2 + eyebrow p）、`dashboard-panel`（含 `panel-primary` + `compact-list`）、以及一组 `holdings-section`（每个含 h3）。

CSS 历史沿革导致两套规则被"分叉式"写在 `apps/web/src/styles.css`：

| 现有成对规则 | 行号 |
|---|---|
| `.detail-page:not(.signal-detail-page) .dashboard-panel` | 693 |
| `.signal-detail-page .dashboard-panel` | 722 |
| `.detail-page:not(.signal-detail-page) .panel-primary` | 701 |
| `.signal-detail-page .panel-primary` | 729 |
| `.holdings-section h3` + `.detail-page:not(.signal-detail-page) .holdings-section h3` + `.signal-detail-page .holdings-section h3` | 1132 / 1139 / 1145 |
| `.compact-list` + `.detail-page .compact-list` + `.signal-detail-page .compact-list` | 739 / 751 / 1092 |

每对规则的属性值大多一致，但 `compact-list dt` 的"标签字号"在两条路径上分叉：
- Signal 路径（1101 行）`.signal-detail-page .compact-list dt`：13px / line-height 1.2 / uppercase / 0.04em
- Backtest 路径（1061 行 `.detail-page dt` + 772 行 `.detail-page .compact-list dt`）：12px / line-height 默认 / uppercase / 0.04em

specificity 计算（id, class, type）——**dt 链**：
- `.compact-list dt` (635) = (0,1,1)
- `.detail-page dt` (1061) = (0,1,1) ← 同分，后写胜
- `.detail-page .compact-list dt` (772) = (0,2,1) ← 比 1061 高一档
- `.signal-detail-page .compact-list dt` (1101) = (0,2,1)

specificity 计算——**dd 链**（apply 阶段补全）：
- `.compact-list dd` (743) = (0,1,1)
- `.detail-page dd` (1059) = (0,1,1) ← 同分，1059 后写胜出（**这就是 15px 漏算的根源**）
- `.detail-page .compact-list dd` (新增 766) = (0,2,1) ← 覆盖 1059
- `.signal-detail-page .compact-list dd` (1101) = (0,2,1) ← Signal 一直在用这条覆盖 1059

**结论**：Backtest 历史上没有 `.detail-page .compact-list dd` 这条覆盖规则，所以被 1059 的 15px 兜底；Signal 一直有 1101 覆盖所以是 13px。这次变更让两边对称，dt 和 dd 都各自有 `.detail-page .compact-list x` 规则覆盖兜底。

Backtest 路径最终值由 1061 决定字号、772 决定 margin-bottom；Signal 路径由 1101 全覆盖 635。结果：Signal `dt` 13px / Backtest `dt` 12px，1px 字号差。

2026-07-05 的 `fix-backtest-detail-field-alignment` 已经处理了"dt 向下偏移 8px / 行间距过大"的对齐问题（772 行重置 `margin-bottom: 0`，751 行重置 gap 到 8px/16px）。本次工作**延续**那次修复的对齐效果，**不**重写 `.detail-page .compact-list dt` 的 `margin-bottom: 0`。

## Goals / Non-Goals

**Goals:**
- Signal Detail 与 Backtest Detail 的 `compact-list dt`（label）使用相同字号 / line-height / 修饰
- 同层元素（page-heading h2 与 p、panel-primary、compact-list dt/dd、holdings-section h3、holdings-table th/td）两页面完全一致
- 合并"分叉式重复"CSS 规则为单条 `.detail-page .x`，让未来调整只改一处
- 保持 2026-07-05 字段对齐修复的视觉效果（dt 与 dd 在每行内 baseline 对齐）

**Non-Goals:**
- 不修改任何 HTML / JSX 结构、组件树、路由、API 客户端
- 不调整 `.dashboard-page` 作用域下任何样式
- 不调整 Backtest 独有元素（`.metric-card`、`.equity-curve-card`、`.equity-curve-summary`、`.parameter-summary`）
- 不调整 holdings-table 的对齐、数字格式、列宽规则
- 不引入新 CSS token、不重命名 `--text-label`（保留以备其他场景使用）

## Decisions

### Decision 1: 对齐到 Signal 的 dt 与 dd 取值（13px / line-height 1.2 / mist color）

把 Backtest 的 `compact-list dt` 和 `compact-list dd` 同时对齐到 Signal 现状（13px / line-height 1.2 / mist color）。**原因**：
- Signal 的 dt 已是 13px / 1.2，Signal 是 2026-07-05 字段对齐修复的"参照物"，没有反馈过 dt 与 dd 不齐
- 对齐到 Signal 等于把"dt 字号 = dd 字号 = 13px"——比 Backtest 现状（dt 13px、dd 15px）的 2px 差距更小
- dt / dd 都使用 `var(--leading-caption)` = 1.2，line-height 完全一致 → grid 行内 baseline 严格对齐
- color 统一为 mist（之前 backtest 是 paper 白，signal 是 mist 浅灰）——同一字段对里 value 和 label 颜色需要协调

**关键事实（apply 阶段发现）**：
- Backtest 的 `compact-list dd` 字号实际是 **15px**（`--text-body`），不是 explore 阶段推断的 13px
- 根源是 `styles.css:1059` 行的 `.detail-page dd { font-size: var(--text-body) }`，specificity (0,1,1) 高于 `.compact-list dd` (0,1,1) 同分后写胜出
- Signal 因为有 `.signal-detail-page .compact-list dd` (0,2,1) 覆盖，所以保持 13px
- **Explore 阶段漏算**——只审计了 dt 对应的 specificity 链，没审计 dd 对应的链；这是 design 的盲点，由用户在浏览器复核中触发

**修复方式**：在 `.detail-page .compact-list dt` 后面新增对称的 `.detail-page .compact-list dd { font-size: var(--text-caption); line-height: var(--leading-caption); color: var(--color-mist); }`，specificity (0,2,1) 覆盖 1059 行。保留 1059 行 `.detail-page dd` 作为"detail 页面其他 dd 的兜底"（虽然目前没有其他 dd 受影响，但保留作为未来扩展安全网）。

**不选 Backtest 现状（12px）作为目标值**：需要把 Signal 改小，会让 Signal 页面看起来"标签更弱"——目前没有动机往那个方向调整。

**不引入新的 1px 中间值（如 12.5px）**：design token 体系只有整数 px，引入小数会破坏 typography scale 的一致性。

### Decision 2: 修改路径选 `.detail-page .compact-list dt`（772 行），**不**改 `.detail-page dt`（1061 行）

1061 行 `.detail-page dt` 的 specificity (0,1,1) 与 635 行 `.compact-list dt` 相同，且 1061 后写，覆盖 635。`compact-list dt` 与其他位置 dt 的差异正在于"label 是否需要 uppercase + 0.04em + 13px"。

- **方案 A（采用）**：保留 1061 行 `.detail-page dt` 作为"detail 页面所有 dt 的兜底"（font-size / transform / letter-spacing / color / weight），把 772 行 `.detail-page .compact-list dt` 升级为完整覆盖（补 font-size / line-height / transform / letter-spacing）。这样 compact-list 之外的 dt 也仍然受 1061 行兜底。
- **方案 B（不采用）**：把 1061 行的 `font-size: var(--text-label)` 改为 `var(--text-caption)`，让 772 行不再需要显式 font-size。**风险**：1061 行还可能影响 detail 页面其他未来 dt（如果有），目前 compact-list 是唯一 dt 来源，但合并会扩大 font-size 改动面。
- **方案 C（不采用）**：把 1061 行整体删掉。**风险**：删后 635 行的 11px / no-transform 生效，会破坏所有 detail 页面的 dt 视觉（fix-backtest-detail-field-alignment 的 design 明确不删）。

选 A 的核心考虑：**改动面最小、行为最可预测**——只在 772 行加 4 行属性，与 1101 行 Signal 规则一一对应（`signal-detail-page` ↔ `detail-page`），合并后差异就是"前缀"。

### Decision 3: 合并"成对重复"规则为单条 `.detail-page .x`，但**分场景差异不合并**

合并前先 audit 两条规则的属性差异。本 change 发现 3 类情况：

**A 类：完全一致 → 直接合并**（如 `.panel-primary` 701/729 两段完全相同）

**B 类：共有属性 + 单边独有属性 → 共有属性合并，独有属性保留为单独规则**（如 `.dashboard-panel` 693/722）
- 693 比 722 多了 `border-radius: var(--radius-md)`，722 没有
- 严格"取并集"会让 signal 页面多出 6px 圆角 → 视觉变化
- 处理：合并的 `.detail-page .dashboard-panel` 只取共有属性（`background`、`border-color`、`min-height`、`padding`）；`border-radius` 单独保留为 `.detail-page:not(.signal-detail-page) .dashboard-panel { border-radius: var(--radius-md) }`

**C 类：差异大到无法安全合并 → 不合并**（如 `.compact-list` 容器 751/1092）
- 751 与 1092 的 `gap`（8/16 vs 12/20）、`margin`（16/0/0 vs 0）、`background`（无 vs obsidian）、`border-radius`（无 vs md）全部不同
- 751 specificity (0,2,0) 高于 1071 `.detail-page dl` (0,1,1)，**覆盖了** row gap 16→8、padding 20→16、margin 24→16——这正是 3ae3088 (fix-backtest-detail-field-alignment) 想保留的视觉
- 删除 751 → backtest 页面回退到 1071 兜底 → 破坏 fix-backtest-detail-field-alignment 修复
- 处理：保留 751 和 1092 作为分场景定义，**不**做合并

**D 类：信号冗余声明 → 合并时直接舍弃**（如 `.holdings-section h3` 1132/1139/1145）
- 1145 多了 `margin-bottom: var(--spacing-12)`，但 1132 基础块已有 `margin: 0 0 var(--spacing-12)` 等价简写
- 1145 的 `margin-bottom` 是冗余声明，合并时舍弃

**通用原则**：
- 合并时**永远取共有属性**作为单条 `.detail-page .x` 的内容，差异属性按 B/C/D 类分别处理
- 不引入新选择器（不引入 `.backtest-detail-page`、不引入 `:where()` 包裹）
- 不改 specificity 数字（即不依赖 `:where()` 把 specificity 降到 0）

**不采用**"用 `:where()` 包裹把 specificity 降到 0"——它会让"防御式分叉"的本意彻底消失，未来如果某个 detail 页面想局部覆盖又得新建 selector，循环。最小特异性 + 合并后的统一规则即可，**够用即好**。

**媒体查询同步检查（强制步骤）**：删除任何 base 规则后，**必须** grep 所有媒体查询块里对该选择器的引用并同步合并——否则响应式断点会失效。base 规则改名/删除 + 媒体查询里残留旧选择器 = 静默的视觉破坏（基础样式不匹配，响应式 padding 也不匹配）。本 change 触发了 3 处媒体查询（1024/900/720）里的 `.detail-page:not(.signal-detail-page) .dashboard-panel, .signal-detail-page .dashboard-panel` 引用，已合并为单条 `.detail-page .dashboard-panel`。

### Decision 4: 不动 `--text-label` token

`--text-label: 12px`（styles.css 89 行）目前只被 1061 行 `.detail-page dt` 一处使用。合并后，1061 行改为引用 `var(--text-caption)`（13px），`--text-label` 变孤儿。

- **方案 A（采用）**：保留 `--text-label`，留作"未来某处需要 12px label"的退路
- **方案 B（不采用）**：删除 `--text-label`，避免"未使用 token"积累

选 A：12px 字号是 typography scale 里的合理值（小于 caption 的"次级标签"），未来若引入新页面需要更小 label 字号，token 现成可用。删除会回退到 hard-code 12px，破坏 token-first 原则。

**注**：本次不写 tasks 把 `--text-label` 标为 unused，audit 范围在本次之外。

### Decision 5: 不补视觉回归测试

前端无 visual regression 套件。回归保障：
- 自动化：`vitest run` 通过
- 人工：浏览器抽样 Signal Detail 与 Backtest Detail，对照 2026-07-05 字段对齐修复的验证方式

**不**新增 Playwright 截图对比或像素 diff——成本与本次改动范围不匹配（CLAUDE.md "Minimum code that solves the problem" 原则）。

## Risks / Trade-offs

- **[Risk] 合并 `.detail-page:not(.signal-detail-page) .x` → `.detail-page .x` 后 specificity 降低一档** → **Mitigation**：手动 audit 所有 `.detail-page` 子规则，确认没有 `.dashboard-page` 作用域下"靠 specificity 覆盖" `.detail-page` 的反向覆盖；若有，保留原写法（不合并）。
- **[Risk] 把 12px → 13px 改变 backtest 详情 label 视觉** → **Mitigation**：13px 与 Signal 一致，是用户明确选择的方向；改动面只是 label，dd / h3 / panel-primary 都不动，整体页面骨架不变。
- **[Risk] 删除"分叉式重复"规则后，git blame 历史不再直接指向 signal-only 改动** → **Mitigation**：commit message 引用 `fix-backtest-detail-field-alignment` 与本 change ID，未来回看 `apps/web/src/styles.css` 时通过 PR 描述即可还原。
- **[Trade-off] CSS 体积减少约 30~50 行**，但**不会**显著改善加载性能——CSS 已经通过 build pipeline gzip，影响忽略。
- **[Trade-off] `--text-label` 暂留为 unused token**，token 列表微冗余；保留它的成本远小于"未来需要 12px 时再找回"的成本。

## Migration Plan

无后端迁移，无 API 变更，无数据迁移。

部署步骤：
1. 修改 `apps/web/src/styles.css`
2. `cd apps/web && npm run build` 确认编译通过
3. `cd apps/web && npx vitest run` 确认测试通过
4. 人工浏览器抽检 Signal Detail 与 Backtest Detail：
   - label 字号/字距/transform 与 dd 字号视觉一致
   - 字段 label 与 value 同行内 baseline 对齐（与 2026-07-05 修复后效果一致）
   - `panel-primary`、h3、eyebrow、h2 在两个页面完全一致

回滚：单文件 CSS 修改，`git revert` 即可。

## Open Questions

无。
