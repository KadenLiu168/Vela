## 1. CSS 修复

- [x] 1.1 添加 `.detail-page .compact-list` 专用规则，覆盖 `.detail-page dl` 的 `gap` 和 `margin` 属性
- [x] 1.2 添加 `.detail-page .compact-list dt` 规则，移除 `margin-bottom` 以确保同行标签和值垂直对齐

## 2. 验证

- [x] 2.1 确认行间距恢复为 8px，字段标签和值在同行内垂直对齐
- [x] 2.2 确认现有功能测试全部通过（`vitest run`）
- [x] 2.3 确认 Signal Detail 和 Dashboard 页面布局不受影响
