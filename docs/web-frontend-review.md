# Vela Web 前端审查报告

> 审查范围：`apps/web`（React 19 + Vite 7 SPA，含设计令牌系统）
> 审查维度：性能 / UI·UX / 代码质量 / 可访问性 / 浏览器兼容性
> 审查结论：**整体架构良好**——设计令牌驱动、语义化充分、错误处理健壮。但存在若干中高危问题，集中在字体格式提示、模态焦点管理、错误边界重置与少量可访问性/重复代码上。

---

## 一、关键问题速览（按优先级）

| 优先级 | 维度 | 问题 | 位置 |
|--------|------|------|------|
| 🔴 高 | 浏览器兼容 | `@font-face` 使用已弃用的 `format("woff2-variations")`，字体在 Chrome 等浏览器无法加载 | `src/styles.css:31` |
| 🟠 中 | 代码质量 | `ErrorBoundary` 路由切换后不重置，`hasError` 残留导致错误兜底常驻 | `src/components/ErrorBoundary.tsx` / `App.tsx` |
| 🟠 中 | 可访问性 | Command Palette 模态无焦点陷阱 + 未用 `aria-activedescendant` | `src/components/CommandPalette.tsx` |
| 🟠 中 | 可访问性 | `color-ash` 小号文字在深色背景对比度约 3.2:1，不达 AA 4.5:1 | `src/styles/tokens.css` / `styles.css` |
| 🟠 中 | 性能 | Command Palette 每次打开重复请求 3 个接口，与 Dashboard 已拉取数据重复 | `CommandPalette.tsx` 176–174 |
| 🟡 低 | 代码质量 | `Detail` / `Metric` / `MetricCard` 在 3 个文件重复定义（违反 DRY） | 各 page 文件 |
| 🟡 低 | UI/UX | 回测日期用 `type="text"` 无原生日期选择器；路由不更新 `document.title`；缺 skip-link | `DashboardPage.tsx` 393–433 |
| 🟡 低 | 代码质量 | 死类/空 handler：`status-surface-empty`、`dashboard-refresh-action`、`onKeyDown={() => {}}` | 多处 |

---

## 二、性能优化

### 2.1 🔴 `@font-face` 格式提示错误（兼属兼容性，见第五节）
`src/styles.css:31`：
```css
src: url("/fonts/InterVariable.woff2") format("woff2-variations");
```
`woff2-variations` 是非标准/已弃用提示，Chrome 已不再识别，会导致该 `@font-face` 声明被忽略、回退系统字体。**直接影响首屏**：变量字体未加载会引发更明显的 FOUT（字体跳动）。改为 `format("woff2")` 即可（变量特性由 woff2 容器本身携带）。

### 2.2 🟠 Command Palette 每次打开重复拉取数据
打开面板（`isOpen` 变 true）时重置并重新请求 `backtests / signal / dashboard` 三个接口（`CommandPalette.tsx` 124–173）。而 Dashboard 挂载时已经请求过 `getDashboard()`，叠加后同一会话内重复请求。
- **优化方向**：把数据提升到 `App` 层或用轻量缓存（如 SWR / React Query / 一个 module 级缓存），面板直接复用，避免重复网络往返与加载态闪烁。

### 2.3 🟡 单包无路由级代码分割
生产 JS 约 234KB 原始 / **71KB gzip**，体积本身可控（React 19 + 全量页面）。但所有页面打包进单一 chunk，无懒加载。
- **优化方向**：对 `DashboardPage / BacktestDetailPage / SignalDetailPage` 使用 `React.lazy` + `Suspense` 按路由拆分，首屏 JS 可进一步下降。

### 2.4 已做得好的部分
- 资源使用内容哈希命名（`index-CJhMi580.js`），利于长期缓存与精确失效。
- 字体 `font-display: swap` + `<link rel="preload" ... crossorigin>` 提前加载关键字体。
- CSS 仅 37KB / **5.8KB gzip**，体积优秀。
- 无位图资源，无未压缩图片拖累。

### 2.5 🟡 生产 `index.html` 缺元数据
`apps/web/dist/index.html` 仅含 title 与字体 preload，缺少 `favicon`、`theme-color`、`meta description`、Web App Manifest。
- **优化方向**：补充 `<link rel="icon">`、`<meta name="theme-color">`、`<meta name="description">`，提升首屏感知与 SEO。

---

## 三、UI / UX 改进

### 3.1 🟠 Command Palette 焦点管理（详见可访问性）
模态对话框 `aria-modal="true"` 但未捕获焦点，键盘 `Tab` 会逃出对话框落到背景元素；选项高亮依赖 window 级键盘处理，但不被读屏播报。

### 3.2 🟡 日期输入体验
`DashboardPage.tsx` 394–423 使用 `<input type="text" inputMode="numeric" placeholder="YYYY-MM-DD">` 而非 `type="date"`：
- 无原生日历控件，移动端需手动输入，易错且对触屏不友好。
- 已有自定义校验（`validateBacktestDates`），可保留校验逻辑但改用原生日期控件。
- **优化方向**：改用 `<input type="date">` 并加 `min/max`；或保留 text 同时增加 `autoComplete="off"` 与更好的输入提示。

### 3.3 🟡 路由标题与导航辅助
- `document.title` 在所有路由都是 "Vela Web"，未随页面更新（SEO/多标签体验）。
- 缺少 "跳到主内容" 跳转链接（skip link），键盘用户每次都需遍历导航。
- **优化方向**：在 `navigate()` 中同步设置 `document.title`；在 `AppShell` 顶部加 `<a class="skip-link" href="#main">`。

### 3.4 已做得好的部分
- 响应式断点完善：`1024 / 900 / 720` 三档，dashboard grid 由 3→2→1 优雅降级，标题/网格/表格在移动端合理堆叠。
- `prefers-reduced-motion` 已处理（`styles.css` 1561–1575）：关闭过渡、骨架动画降级为静态。
- 深色主题统一，间距/排版由设计令牌驱动，视觉一致性强。

---

## 四、代码质量

### 4.1 🟠 ErrorBoundary 路由切换后不重置（功能 bug）
`App.tsx` 用同一个 `ErrorBoundary` 实例包裹 `{renderRoute(path, ...)}`。页面渲染抛错后 `getDerivedStateFromError` 将 `hasError` 置 true 并显示兜底；导航到其他路由时 `children` 变化但 `ErrorBoundary` 实例不变，`hasError` 仍为真——**错误兜底会常驻，即使已离开出错的页面**。
- **优化方向**：给 `ErrorBoundary` 加 `key={path}`（随路由重建），或在 `componentDidUpdate` 中按 `path` 重置 `hasError`。

### 4.2 🟡 重复组件（违反 DRY）
`Detail` 在 `DashboardPage.tsx:1014`、`SignalDetailPage.tsx:143`、`BacktestDetailPage.tsx:263` 三处定义；`Metric`/`MetricCard` 也重复。
- **优化方向**：抽到 `components/` 共享（如 `FieldList`、`MetricCard`），三页统一引用，降低维护成本与样式漂移风险。

### 4.3 🟡 `formatDate` 实现脆弱
`utils/formatters.ts:18`：`return value.slice(0, 10);` 直接截断前 10 字符，不校验、不解析。若接口返回带时区或非 ISO 字符串会静默显示错误或截断。
- **优化方向**：改用 `Intl.DateTimeFormat` 或 `new Date(value)` 解析后再格式化，并对非法值回退 `EMPTY_VALUE`。

### 4.4 🟡 Command Palette 的 ref 镜像模式过重
为维持常驻 `keydown` handler，使用了 9 个 `useRef` 镜像最新状态（`isOpenRef / onCloseRef / onNavigateRef / visibleRowsRef / expandedEtfIdRef / setExpandedEtfIdRef / setActiveRowIdRef / validActiveRowIdRef / previousActiveElement`）。可维护性差、易出错。
- **优化方向**：合并为单一 `stateRef` 对象；或直接将依赖列入 effect 依赖（用合成而非 ref 镜像），让 handler 随状态更新重绑。

### 4.5 🟡 死代码 / 冗余
- `CommandPalette.tsx:300` 与 `:363` 的 `onKeyDown={() => {}}` 是空处理函数，应删除。
- `FeedbackMessage.tsx:23` 的 `status-surface-empty` 与 `DashboardPage.tsx:245` 的 `dashboard-refresh-action` 类被使用但**无对应 CSS 规则**（注释明说样式已移除）——属冗余/迷惑性类名。
- `Skeleton.tsx` 同时设 `aria-hidden="true"` 与 `role="presentation"`，二者重复。

### 4.6 已做得好的部分
- API client 错误处理健壮：分类错误（`validation/not_found/operation_failed/network`）、网络错误、JSON 解析容错（`getApiError`）一应俱全。
- 类型定义完整，TS 严格模式（`tsc -b`）把关。
- 列表/详情页的加载态、错误态、空态、404 态分支清晰。

---

## 五、可访问性（Accessibility）

### 5.1 🟠 模态焦点陷阱 + 读屏播报缺失（命令面板）
- `aria-modal="true"` 但无焦点陷阱，`Tab` 逃出对话框。
- 选项 `role="option"` 且 `tabIndex={-1}`，高亮项未被 `aria-activedescendant` 指向，**读屏不会播报当前选中项**。
- **优化方向**：①用 focus trap（或 `inert` 背景）把焦点锁在面板内；②在 input 上设 `aria-activedescendant={validActiveRowId}`，并给每个 option 稳定 `id`，构成标准 combobox/listbox 模式。

### 5.2 🟠 `color-ash` 文字对比度不达标
`--color-ash: #62666d` 用于 `.command-palette-row-kind`（小号大写 meta）与输入框占位符，深色背景上对比度约 **3.2:1**，低于 WCAG AA 对正文文本的 4.5:1 要求。
- **优化方向**：文字类使用 `--color-fog`(#8a8f98，约 5.6:1) 或提亮 ash；占位符至少接近 4.5:1。

### 5.3 已做得好的部分
- **全站无缺失 `alt`**：未使用任何 `<img>` 位图；SVG 净值曲线图用 `role="img"` + `<title>` 提供可访问名称。
- 表单 label 用 `<label>` 包裹 `<input>`，隐式关联正确；命令输入框有 `aria-label="Search"`。
- `FeedbackMessage` 用 `aria-live="polite"`（错误态为 `role="alert"`），状态变化可被读屏播报。
- 语义充分：`<nav aria-label>`、`aria-current="page"`、`<time dateTime>`、`<table>` 配 `<th scope="col">`、各区块 `<section aria-labelledby>`。
- `:where(a, button, input):focus-visible` 提供清晰聚焦环（2px + offset）。

---

## 六、浏览器兼容性

### 6.1 🔴 `format("woff2-variations")`（高危，必改）
见 2.1 / 5 章开头。`woff2-variations` 提示已弃用且不被现代浏览器识别，会导致 Inter Variable 字体声明失效，回退系统字体并可能引发 FOUT。
- **修复**：`format("woff2")`。

### 6.2 🟡 渐进增强特性（无需修改）
- `text-wrap: balance`（标题 `styles.css:573` 等）：仅 2023+ 浏览器支持，旧浏览器忽略，优雅降级。
- `:where()` 选择器（`styles.css:58`）：现代浏览器（2021+）支持；极旧浏览器（如 Safari <14.1）可能不生效，导致 `box-sizing` 全局规则失效——可接受，如需兼容旧版可去掉 `:where()`。

### 6.3 已做得好的部分
- 未使用任何实验性/已弃用 API。所用 `Array.flatMap`、`URLSearchParams`、`Intl.NumberFormat`、`Promise.allSettled`、`fetch`、`requestAnimationFrame` 均为广泛支持的标准。
- 语义化 HTML 为主，兼容性风险低。

---

## 七、建议落地顺序

1. **立即修**：`@font-face` 改为 `format("woff2")`（兼容性 + 首屏字体）。
2. **尽快修**：`ErrorBoundary` 加 `key={path}` 重置；命令面板加焦点陷阱 + `aria-activedescendant`。
3. **本迭代**：提取共享 `Detail/Metric` 组件；`formatDate` 用 `Intl.DateTimeFormat`；面板数据加缓存避免重复请求；`color-ash` 文字改用更高对比色。
4. **后续打磨**：路由级懒加载、skip-link、`document.title` 更新、日期输入改用 `type="date"`、补 `index.html` 元数据、清理死类/空 handler。

---
*审查人：UI Designer（前端设计审查）· 2026-07-07*
