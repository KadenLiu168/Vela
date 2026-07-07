## 1. 更新设计 Token

- [x] 1.1 修改 `apps/web/src/styles/tokens.css` 中 `--font-display` 的值链：`"IBM Plex Mono", "Söhne Mono"` → `"Inter Variable", "Söhne Mono"`
- [x] 1.2 修改 `apps/web/src/styles/tokens.css` 中 `--font-berkeley-mono` 的值链：`"IBM Plex Mono", "Berkeley Mono"` → `"Inter Variable", "Berkeley Mono"`
- [x] 1.3 更新 `apps/web/src/styles/tokens.css` 中两个 token 相关的注释块

## 2. 清理 IBM Plex Mono 字体

- [x] 2.1 从 `apps/web/src/styles.css` 中删除 IBM Plex Mono 的三个 `@font-face` 声明（Regular / Medium / SemiBold）
- [x] 2.2 从 `apps/web/public/fonts/` 中删除 `IBMPlexMono-Regular.woff2`、`IBMPlexMono-Medium.woff2`、`IBMPlexMono-SemiBold.woff2`
- [x] 2.3 从 `apps/web/index.html` 中删除 IBM Plex Mono 的两个 `<link rel="preload">` 元素
- [x] 2.4 更新 `apps/web/src/styles.css` 顶部注释块关于字体清单的说明
- [x] 2.5 清理构建产物中 IBM Plex Mono 的缓存文件

## 3. 构建验证

- [x] 3.1 执行 `vite build` 确认构建成功
- [x] 3.2 验证构建产物的 CSS 中 `--font-display` 和 `--font-berkeley-mono` 值正确

## 4. 更新 OpenSpec Spec

- [ ] 4.1 归档 `openspec/changes/unify-font-to-inter-variable/specs/design-system/spec.md` 到 `openspec/specs/design-system/spec.md`

## 5. 收尾

- [ ] 5.1 提交代码并附带清晰的 commit message
- [ ] 5.2 标记 OpenSpec change 为 `done`
