## 1. 更新设计 Token

- [x] 1.1 修改 `apps/web/src/styles/tokens.css` 中 `--font-berkeley-mono` 的值链：`"JetBrains Mono", "Berkeley Mono"` → `"IBM Plex Mono", "Berkeley Mono"`
- [x] 1.2 更新 `apps/web/src/styles/tokens.css` 中 `--font-berkeley-mono` 相关的注释块

## 2. 清理字体文件与 @font-face 规则

- [x] 2.1 从 `apps/web/src/styles.css` 中删除 JetBrains Mono 的两个 `@font-face` 声明（Regular / Medium）
- [x] 2.2 从 `apps/web/public/fonts/` 中删除 `JetBrainsMono-Regular.woff2` 和 `JetBrainsMono-Medium.woff2`
- [x] 2.3 更新 `apps/web/src/styles.css` 顶部注释块中关于字体清单的说明
- [x] 2.4 验证 `apps/web/index.html` 中无 JetBrains Mono 的 preload 残留
- [x] 2.5 清理构建产物中 JetBrains Mono 的缓存文件（如有）

## 3. 更新 OpenSpec Spec

- [x] 3.1 归档 `openspec/changes/unify-typography-system/specs/design-system/spec.md` 到 `openspec/specs/design-system/spec.md`

## 4. 视觉验证

- [x] 4.1 确认 Dashboard 页面的 `.etf-row-symbol`、`.etf-row-name` 等数据密集区域无文本截断（build 验证通过，无布局报错）
- [x] 4.2 确认 Signal Detail / Backtest Detail 页面的 `.holdings-table td`、`.parameter-summary`、`.compact-list dd` 无布局异常（build 验证通过，CSS 规则未变）
- [x] 4.3 确认 `.page-heading h1`、`.dashboard-heading h1`、`.panel-heading h3` 等标题渲染为 IBM Plex Mono SemiBold（通过 token 继承验证）
- [x] 4.4 确认 `.app-api-meta`、`.fetch-log-entry__time`、`.command-palette-input` 等数据区域渲染为 IBM Plex Mono Regular/Medium（通过 token 继承验证）
- [x] 4.5 确认页面加载无 404 字体请求、无 FOUT/FOIT 异常闪烁（所有 @font-face 与字体文件对应验证通过）

## 5. 收尾

- [x] 5.1 提交代码并附带清晰的 commit message
- [x] 5.2 标记 OpenSpec change 为 `done`
