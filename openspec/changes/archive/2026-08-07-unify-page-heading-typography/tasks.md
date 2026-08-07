## 1. 更新共享标题基础规则

- [x] 1.1 修改 `apps/web/src/styles.css` 中 `.page-heading h1` 基础规则（约 181-189 行）：`font-size` 从 `var(--text-heading)` 改为 `var(--text-heading-sm)`，`letter-spacing` 从 `var(--tracking-heading)` 改为 `var(--tracking-heading-sm)`，`line-height` 从 `var(--leading-heading)` 改为 `var(--leading-heading-sm)`；`font-family`、`font-weight`、`color`、`margin` 保持不变

## 2. 删除冗余覆盖规则

- [x] 2.1 删除 `apps/web/src/styles.css` 中 `.dashboard-heading h1` 覆盖块（约 203-208 行），其字号/字距/行高已与新的基础规则一致；保留 `.dashboard-heading` 布局规则（约 191-197 行，flex、gap、justify-content、max-width）
- [x] 2.2 删除 `apps/web/src/styles.css` `@media (width <= 720px)` 内的 `.page-heading h1` 覆盖（约 2037-2041 行），避免移动端标题回退到 48px 与 Dashboard 不一致

## 3. 同步 OpenSpec spec

- [x] 3.1 将 `openspec/specs/design-system/spec.md` 中 "Dashboard heading uses a discrete responsive ladder" 需求替换为"全站 `page-heading h1` 统一使用 `var(--text-heading-sm)`"的表述（与 change 的 delta spec 内容一致）
- [x] 3.2 将 `openspec/specs/detail-page-typography-consistency/spec.md` 中"跨页面同层元素 typography 一致"需求的标题部分更新为覆盖全部 `page-heading h1` 页面、统一尺寸 `var(--text-heading-sm)`（与 change 的 delta spec 内容一致）

## 4. 验证

- [x] 4.1 运行 `openspec validate unify-page-heading-typography --strict`，确认 delta spec 与现有 spec 匹配（header 精确匹配、场景格式合法）
- [x] 4.2 检查页面测试是否断言标题样式或字号（如 `DashboardPage.test.tsx`、`SignalListPage.test.tsx`、`WalkForwardListPage.test.tsx`），如有相关断言则同步更新
- [x] 4.3 从仓库根目录运行 Web gate：`npm --prefix apps/web run lint`、`npm --prefix apps/web run lint:css`、`npm --prefix apps/web run typecheck`、`npm --prefix apps/web run test`、`npm --prefix apps/web run build`
- [x] 4.4 人工确认各页面（Dashboard、Signal List/Detail、Backtest List/Detail、Walk-forward List/Detail、ETF Detail）标题字号一致（32px），Dashboard 视觉无变化
