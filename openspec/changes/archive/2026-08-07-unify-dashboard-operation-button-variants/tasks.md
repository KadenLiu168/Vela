## 1. 修改按钮类名

- [x] 1.1 将 `apps/web/src/pages/DashboardPage.tsx` 第 390 行 "Fetch full" 按钮的 `className` 从 `button-tertiary` 改为 `button-secondary`（保留 `title` 与文案不变）

## 2. 同步 OpenSpec spec

- [x] 2.1 将 `openspec/specs/design-system/spec.md` 中 "Buttons follow a three-variant contract" 需求补充"同一 `.operation-list` 组内按钮 MUST 使用 `secondary` 档位，不得与 `tertiary` 混排"的约束与场景（与 change 的 delta spec 内容一致）

## 3. 验证

- [x] 3.1 运行 `openspec validate unify-dashboard-operation-button-variants --strict`，确认 delta spec 匹配
- [x] 3.2 运行 `npm --prefix apps/web run test -- DashboardPage` 检查按钮类名相关断言，如有则同步更新
- [x] 3.3 从仓库根目录运行完整 Web gate：`npm --prefix apps/web run lint`、`npm --prefix apps/web run lint:css`、`npm --prefix apps/web run typecheck`、`npm --prefix apps/web run test`、`npm --prefix apps/web run build`
- [x] 3.4 人工确认 Dashboard Operations 面板中 "Fetch full" 与其他操作按钮视觉一致（同为 outline 描边）
