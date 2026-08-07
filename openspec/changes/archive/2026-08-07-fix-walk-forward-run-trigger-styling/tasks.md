## 1. 修改 run-trigger 按钮与容器

- [x] 1.1 将 `apps/web/src/pages/WalkForwardListPage.tsx` 第 155 行 "Run walk-forward" 按钮的 `className` 从 `action-button` 改为 `button-secondary`
- [x] 1.2 在 `apps/web/src/styles.css` 新增 `.walk-forward-run-trigger { margin-bottom: var(--spacing-16); }` 规则（放置于按钮/列表相关规则附近）

## 2. 同步 OpenSpec spec

- [x] 2.1 将 `openspec/specs/web-frontend-app/spec.md` 中 "Walk-forward list page provides run trigger" 需求补充"run trigger 使用合法变体类名 + 容器间距"的约束与场景（与 change 的 delta spec 内容一致）

## 3. 验证

- [x] 3.1 运行 `openspec validate fix-walk-forward-run-trigger-styling --strict`，确认 delta spec 匹配
- [x] 3.2 运行 `npm --prefix apps/web run test -- WalkForwardListPage` 检查按钮类名相关断言，如有则同步更新
- [x] 3.3 从仓库根目录运行完整 Web gate：`npm --prefix apps/web run lint`、`npm --prefix apps/web run lint:css`、`npm --prefix apps/web run typecheck`、`npm --prefix apps/web run test`、`npm --prefix apps/web run build`
- [x] 3.4 人工确认 Walk-forward 列表页 run-trigger 按钮呈现 `secondary` 描边样式，与表格间距对齐
