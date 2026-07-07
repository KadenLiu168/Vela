## Why

Web frontend 当前加载了三套字体（Inter Variable、JetBrains Mono、IBM Plex Mono），其中 JetBrains Mono 和 IBM Plex Mono 作为等宽字体视觉差异过小，造成"两个字体长得很像但又不是同一个"的视觉混乱。三套字体架构缺乏清晰的层级逻辑，影响了设计系统的一致性。需要精简为两套字体，用字重和尺寸来制造视觉层级，消除混乱。

## What Changes

1. **移除 JetBrains Mono 字体** — 删除两套 @font-face 声明及其 woff2 字体文件，停止加载和使用 JetBrains Mono
2. **更新 `--font-berkeley-mono` token** — 指向 IBM Plex Mono，使该 token 从 JetBrains Mono 切换为已加载的 IBM Plex Mono
3. **统一等宽字体为 IBM Plex Mono** — `--font-display` 和 `--font-berkeley-mono` 同源（IBM Plex Mono），通过字重（Regular / Medium / SemiBold）区分标题、数据、标签层级
4. **更新 OpenSpec design-system spec** — 反映新的等宽字体 token 值链
5. **清理所有文档注释** — styles.css 和 tokens.css 中的字体文档
6. **精简字体文件** — 减少 182KB 字体体积（JetBrains Mono 两个 woff2 文件）

## Capabilities

### New Capabilities

_无 — 这是设计系统内部的精简优化，不引入新能力。_

### Modified Capabilities

- `design-system`: `--font-berkeley-mono` token 值链从 `"JetBrains Mono", "Berkeley Mono", ...` 改为 `"IBM Plex Mono", "Berkeley Mono", ...`；`--font-display` 和 `--font-berkeley-mono` 统一为 IBM Plex Mono。
- `card-type-scale`: 无 requirement 变化，仅字体族消费值随 token 变化自动切换。
- `detail-page-typography-consistency`: 无 requirement 变化，仅字体族消费值随 token 变化自动切换。

## Impact

- **前端体积**：-182KB（删除两个 JetBrains Mono woff2）
- **CSS**：14处 `var(--font-berkeley-mono)` 消费者无需修改代码，token 值变化自动继承
- **字体加载**：减少两个 preload（目前没有 JetBrains 的 preload，无需清理）
- **视觉影响**：数据密集区域（ETF 代码、时间戳、数值）字宽略增（IBM Plex Mono 略宽于 JetBrains Mono），可能需要检查布局有无截断
- **设计系统 spec**：需更新 `design-system` spec 中关于等宽字体 token 的 requirement
- **不再依赖 JetBrains Mono**：字体文件夹清除两个 woff2 文件
