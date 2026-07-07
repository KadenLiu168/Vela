## 1. 测试断言修正

- [ ] 1.1 `App.test.tsx` line 38: `getByText("Earliest trade date")` → `getByText("Earliest")`
- [ ] 1.2 `App.test.tsx` line 40: `getByText("Latest trade date")` → `getByText("Latest")`
- [ ] 1.3 `App.test.tsx` line 224: `getAllByText("n/a").toHaveLength(2)` → `queryAllByText("n/a").toHaveLength(0)`

## 2. 验证

- [ ] 2.1 运行 `npx vitest run` 全量通过（0 failures）
- [ ] 2.2 运行 `npm run typecheck` 类型检查通过
- [ ] 2.3 运行 `openspec validate --all` 通过
