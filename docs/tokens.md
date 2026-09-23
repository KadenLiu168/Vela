# Vela Web — Design Tokens Reference

> Auto-generated from `apps/web/src/styles/tokens.css` by `scripts/build-tokens-reference.mjs`.
> Regenerate after editing tokens.css: `npm --prefix apps/web run build:tokens-doc`.

## Table of Contents

- [1. Surfaces — Celestial Research dark stack](#1-surfaces-celestial-research-dark-stack)
- [2. Borders](#2-borders)
- [3. Text](#3-text)
- [4. Interaction — Celestial Blue is reserved for interaction identity](#4-interaction-celestial-blue-is-reserved-for-interaction-identity)
- [5. Status — operation outcomes and system feedback](#5-status-operation-outcomes-and-system-feedback)
- [6. China market — positive is red, negative is green, flat is neutral](#6-china-market-positive-is-red-negative-is-green-flat-is-neutral)
- [7. Charts — chart primitives and the categorical series palette](#7-charts-chart-primitives-and-the-categorical-series-palette)
- [8. Typography families — Geist Sans for language, Geist Mono for data](#8-typography-families-geist-sans-for-language-geist-mono-for-data)
- [9a. Card type ladder — owned by `card-type-scale` capability](#9a-card-type-ladder-owned-by-card-type-scale-capability)
- [10. Spacing — 4px base unit (rem, equal at default 16px root font)](#10-spacing-4px-base-unit-rem-equal-at-default-16px-root-font)
- [10a. Spacing — 8px-grid semantic ladder (preferred for layout gaps)](#10a-spacing-8px-grid-semantic-ladder-preferred-for-layout-gaps)
- [12. Border radius — primitives](#12-border-radius-primitives)
- [13. Shadows](#13-shadows)
- [14. Motion vocabulary](#14-motion-vocabulary)
- [15. Card primitives — shared by .panel-primary, .dashboard-card,
     .metric-card, and similar surfaces. Standard research panels select the
     panel surface explicitly (see --panel-bg); raised stays reserved for
     emphasized metrics and floating layers. Surface contrast plus border is
     the primary hierarchy mechanism; panels carry no shadow.](#15-card-primitives-shared-by-panel-primary-dashboard-card-metric-card-and-similar-surfaces-standard-research-panels-select-the-panel-surface-explicitly-see-panel-bg-raised-stays-reserved-for-emphasized-metrics-and-floating-layers-surface-contrast-plus-border-is-the-primary-hierarchy-mechanism-panels-carry-no-shadow)

## 1. Surfaces — Celestial Research dark stack

| Token | Value | Resolved |
| --- | --- | --- |
| `--surface-canvas` | `#090c12` |  |
| `--surface-panel` | `#0f141d` |  |
| `--surface-raised` | `#151c28` |  |
| `--surface-hover` | `#1c2533` |  |

## 2. Borders

| Token | Value | Resolved |
| --- | --- | --- |
| `--border-subtle` | `#263244` |  |
| `--border-strong` | `#35445a` |  |

## 3. Text

| Token | Value | Resolved |
| --- | --- | --- |
| `--text-primary` | `#f4f7fb` |  |
| `--text-secondary` | `#b7c0ce` |  |
| `--text-tertiary` | `#7f8a9a` |  |

## 4. Interaction — Celestial Blue is reserved for interaction identity

| Token | Value | Resolved |
| --- | --- | --- |
| `--interactive-primary` | `#6d8eff` |  |
| `--interactive-primary-hover` | `#87a4ff` |  |
| `--interactive-primary-pressed` | `#587af2` |  |
| `--focus-ring-color` | `#87a4ff` |  |

## 5. Status — operation outcomes and system feedback

| Token | Value | Resolved |
| --- | --- | --- |
| `--status-success` | `#45d483` |  |
| `--status-warning` | `#f6c85f` |  |
| `--status-danger` | `#ff5c7a` |  |
| `--status-info` | `#52c7ea` |  |

## 6. China market — positive is red, negative is green, flat is neutral

| Token | Value | Resolved |
| --- | --- | --- |
| `--market-up` | `#ff7a59` |  |
| `--market-down` | `#2fc6a2` |  |
| `--market-flat` | `#b7c0ce` |  |

## 7. Charts — chart primitives and the categorical series palette

| Token | Value | Resolved |
| --- | --- | --- |
| `--chart-primary-line` | `#7c9cff` |  |
| `--chart-grid` | `#263244` |  |
| `--chart-axis` | `#7f8a9a` |  |
| `--chart-crosshair` | `#7f8a9a` |  |
| `--chart-series-1` | `#7c9cff` |  |
| `--chart-series-2` | `#46c2b3` |  |
| `--chart-series-3` | `#f3c969` |  |
| `--chart-series-4` | `#d88cff` |  |
| `--chart-series-5` | `#ff8a65` |  |
| `--chart-series-6` | `#8fcb6a` |  |

## 8. Typography families — Geist Sans for language, Geist Mono for data

| Token | Value | Resolved |
| --- | --- | --- |
| `--font-sans` | `"Geist Sans", ui-sans-serif, system-u...` |  |
| `--font-mono` | `"Geist Mono", "SFMono-Regular", "Casc...` |  |
| `--text-page-title` | `2.25rem` |  |
| `--leading-page-title` | `2.5rem` |  |
| `--text-page-title-compact` | `1.75rem` |  |
| `--leading-page-title-compact` | `2.25rem` |  |
| `--text-section-title` | `1.375rem` |  |
| `--leading-section-title` | `1.75rem` |  |
| `--text-card-title` | `1rem` |  |
| `--leading-card-title` | `1.375rem` |  |
| `--text-metric-hero` | `2rem` |  |
| `--leading-metric-hero` | `2.25rem` |  |
| `--text-metric` | `1.5rem` |  |
| `--leading-metric` | `1.875rem` |  |
| `--text-body` | `0.9375rem` |  |
| `--leading-body` | `1.375rem` |  |
| `--text-dense` | `0.8125rem` |  |
| `--leading-dense` | `1.25rem` |  |
| `--text-label` | `0.75rem` |  |
| `--leading-label` | `1rem` |  |
| `--text-meta` | `0.6875rem` |  |
| `--leading-meta` | `1rem` |  |
| `--text-chart-axis` | `0.6875rem` |  |
| `--leading-chart-axis` | `1rem` |  |
| `--tracking-meta` | `0.06em` |  |
| `--tracking-numeral` | `-0.01em` |  |
| `--tracking-title` | `-0.035em` |  |

## 9a. Card type ladder — owned by `card-type-scale` capability

| Token | Value | Resolved |
| --- | --- | --- |
| `--card-meta-size` | `var(--text-meta)` | → `0.6875rem` |
| `--card-body-size` | `var(--text-dense)` | → `0.8125rem` |
| `--card-emphasis-size` | `var(--text-metric)` | → `1.5rem` |
| `--card-display-size` | `var(--text-metric-hero)` | → `2rem` |
| `--leading-body-card` | `1.25rem` |  |
| `--leading-emphasis` | `var(--leading-metric)` | → `1.875rem` |
| `--leading-display-card` | `var(--leading-metric-hero)` | → `2.25rem` |
| `--font-weight-regular` | `400` |  |
| `--font-weight-axis` | `450` |  |
| `--font-weight-medium` | `520` |  |
| `--font-weight-label` | `560` |  |
| `--font-weight-title` | `580` |  |
| `--font-weight-brand` | `620` |  |

## 10. Spacing — 4px base unit (rem, equal at default 16px root font)

| Token | Value | Resolved |
| --- | --- | --- |
| `--spacing-unit` | `0.25rem` |  |
| `--spacing-4` | `0.25rem` |  |
| `--spacing-8` | `0.5rem` |  |
| `--spacing-12` | `0.75rem` |  |
| `--spacing-16` | `1rem` |  |
| `--spacing-20` | `1.25rem` |  |
| `--spacing-24` | `1.5rem` |  |
| `--spacing-32` | `2rem` |  |
| `--spacing-36` | `2.25rem` |  |
| `--spacing-40` | `2.5rem` |  |
| `--spacing-48` | `3rem` |  |
| `--spacing-56` | `3.5rem` |  |
| `--spacing-60` | `3.75rem` |  |
| `--spacing-64` | `4rem` |  |
| `--spacing-80` | `5rem` |  |
| `--spacing-96` | `6rem` |  |
| `--spacing-128` | `8rem` |  |

## 10a. Spacing — 8px-grid semantic ladder (preferred for layout gaps)

| Token | Value | Resolved |
| --- | --- | --- |
| `--space-xs` | `var(--spacing-8)` | → `0.5rem` |
| `--space-sm` | `var(--spacing-16)` | → `1rem` |
| `--space-md` | `var(--spacing-24)` | → `1.5rem` |
| `--space-lg` | `var(--spacing-32)` | → `2rem` |
| `--space-xl` | `var(--spacing-48)` | → `3rem` |
| `--space-2xl` | `var(--spacing-64)` | → `4rem` |
| `--space-3xl` | `var(--spacing-96)` | → `6rem` |
| `--page-max-width` | `1200px` |  |
| `--section-gap` | `var(--space-xl)` | → `3rem` |
| `--section-gap-compact` | `var(--space-lg)` | → `2rem` |
| `--group-gap` | `var(--space-md)` | → `1.5rem` |
| `--heading-content-gap` | `var(--space-md)` | → `1.5rem` |
| `--page-gutter-wide` | `var(--space-lg)` | → `2rem` |
| `--page-gutter-medium` | `var(--space-md)` | → `1.5rem` |
| `--page-gutter-compact` | `var(--space-sm)` | → `1rem` |
| `--card-padding` | `var(--space-md)` | → `1.5rem` |
| `--element-gap` | `var(--spacing-8)` | → `0.5rem` |
| `--control-min-height` | `2.25rem` |  |
| `--control-touch-size` | `2.75rem` |  |

## 12. Border radius — primitives

| Token | Value | Resolved |
| --- | --- | --- |
| `--radius-sm` | `2px` |  |
| `--radius-md` | `6px` |  |
| `--radius-xl` | `12px` |  |
| `--radius-2xl` | `16px` |  |
| `--radius-2xl-2` | `22px` |  |
| `--radius-full` | `400px` |  |
| `--radius-full-2` | `9999px` |  |
| `--radius-small` | `2px` |  |
| `--radius-badges` | `4px` |  |
| `--radius-inputs` | `6px` |  |
| `--radius-buttons` | `6px` |  |
| `--radius-cards` | `12px` |  |
| `--radius-pills` | `9999px` |  |

## 13. Shadows

| Token | Value | Resolved |
| --- | --- | --- |
| `--shadow-sm` | `rgba(0, 0, 0, 0.4) 0px 2px 4px 0px` |  |
| `--shadow-md` | `rgba(0, 0, 0, 0.2) 0px 0px 12px 0px i...` |  |
| `--shadow-subtle` | `rgb(35, 37, 42) 0px 0px 0px 1px inset` |  |
| `--shadow-subtle-2` | `rgba(0, 0, 0, 0.2) 0px 0px 0px 1px` |  |
| `--shadow-subtle-3` | `rgba(0, 0, 0, 0.01) 0px 5px 2px 0px, ...` |  |
| `--shadow-xl` | `rgba(8, 9, 10, 0.6) 0px 4px 32px 0px` |  |
| `--shadow-subtle-4` | `rgba(255, 255, 255, 0.03) 0px 0px 0px...` |  |
| `--shadow-subtle-5` | `rgba(0, 0, 0, 0.1) 0px 0px 0px 2px` |  |

## 14. Motion vocabulary

| Token | Value | Resolved |
| --- | --- | --- |
| `--duration-fast` | `120ms` |  |
| `--duration-base` | `200ms` |  |
| `--duration-slow` | `320ms` |  |
| `--ease-out` | `cubic-bezier(0.2, 0, 0, 1)` |  |

## 15. Card primitives — shared by .panel-primary, .dashboard-card,
     .metric-card, and similar surfaces. Standard research panels select the
     panel surface explicitly (see --panel-bg); raised stays reserved for
     emphasized metrics and floating layers. Surface contrast plus border is
     the primary hierarchy mechanism; panels carry no shadow.

| Token | Value | Resolved |
| --- | --- | --- |
| `--card-bg` | `var(--surface-raised)` | → `#151c28` |
| `--panel-bg` | `var(--surface-panel)` | → `#0f141d` |
| `--card-border-color` | `var(--border-subtle)` | → `#263244` |
| `--card-padding-x` | `var(--space-md)` | → `1.5rem` |
| `--card-padding-y` | `var(--space-md)` | → `1.5rem` |
| `--card-padding-compact` | `var(--space-sm)` | → `1rem` |
| `--card-radius` | `var(--radius-cards)` | → `12px` |
| `--card-shadow` | `none` |  |
| `--card-gap` | `var(--element-gap)` | → `0.5rem` |
