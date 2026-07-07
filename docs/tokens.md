# Vela Web — Design Tokens Reference

> Auto-generated from `apps/web/src/styles/tokens.css` by `scripts/build-tokens-reference.mjs`.
> Regenerate after editing tokens.css: `npm --prefix apps/web run build:tokens-doc`.

## Table of Contents

- [1. Colors — Linear midnight palette](#1-colors-linear-midnight-palette)
- [2. Surfaces — dark stack (aliases onto color tokens)](#2-surfaces-dark-stack-aliases-onto-color-tokens)
- [3. Typography families](#3-typography-families)
- [4. Typography scale](#4-typography-scale)
- [5. Font weights — Vela semantic aliases onto Inter Variable values](#5-font-weights-vela-semantic-aliases-onto-inter-variable-values)
- [6. Spacing — 4px base unit](#6-spacing-4px-base-unit)
- [6a. Spacing — 8px-grid semantic ladder (preferred for layout gaps).
     Each rung aliases an existing 8px-grid primitive so the ladder
     re-tunes automatically if the primitive ever changes.](#6a-spacing-8px-grid-semantic-ladder-preferred-for-layout-gaps-each-rung-aliases-an-existing-8px-grid-primitive-so-the-ladder-re-tunes-automatically-if-the-primitive-ever-changes)
- [7. Layout](#7-layout)
- [8. Border radius — primitives](#8-border-radius-primitives)
- [9. Shadows](#9-shadows)
- [10. Feedback accents and focus ring](#10-feedback-accents-and-focus-ring)
- [11. Motion vocabulary](#11-motion-vocabulary)
- [12. Font features — Inter Variable OT features for default text](#12-font-features-inter-variable-ot-features-for-default-text)
- [13. Card primitives — shared by .panel-primary, .dashboard-card,
     .metric-card, and similar surfaces. Aliases onto existing primitives;
     consumer migration is the follow-up `design-system-component-polish`.](#13-card-primitives-shared-by-panel-primary-dashboard-card-metric-card-and-similar-surfaces-aliases-onto-existing-primitives-consumer-migration-is-the-follow-up-design-system-component-polish)

## 1. Colors — Linear midnight palette

| Token | Value | Resolved |
| --- | --- | --- |
| `--color-void` | `#08090a` |  |
| `--color-carbon` | `#0f1011` |  |
| `--color-obsidian` | `#161718` |  |
| `--color-graphite` | `#23252a` |  |
| `--color-smoke` | `#383b3f` |  |
| `--color-ash` | `#62666d` |  |
| `--color-fog` | `#8a8f98` |  |
| `--color-mist` | `#d0d6e0` |  |
| `--color-bone` | `#e5e5e6` |  |
| `--color-paper` | `#fff` |  |
| `--color-acid-lime` | `#e4f222` |  |
| `--color-pulse-green` | `#27a644` |  |
| `--color-coral-red` | `#eb5757` |  |
| `--color-signal-teal` | `#02b8cc` |  |
| `--color-iris-violet` | `#6366f1` |  |
| `--color-lavender` | `#8b5cf6` |  |

## 2. Surfaces — dark stack (aliases onto color tokens)

| Token | Value | Resolved |
| --- | --- | --- |
| `--surface-void` | `var(--color-void)` | → `#08090a` |
| `--surface-carbon` | `var(--color-carbon)` | → `#0f1011` |
| `--surface-obsidian` | `var(--color-obsidian)` | → `#161718` |
| `--surface-slate` | `var(--color-graphite)` | → `#23252a` |

## 3. Typography families

| Token | Value | Resolved |
| --- | --- | --- |
| `--font-inter-variable` | `"Inter Variable", ui-sans-serif, syst...` |  |
| `--font-berkeley-mono` | `"JetBrains Mono", "Berkeley Mono", ui...` |  |

## 4. Typography scale

| Token | Value | Resolved |
| --- | --- | --- |
| `--text-caption` | `13px` |  |
| `--leading-caption` | `1.2` |  |
| `--text-body-sm` | `15px` |  |
| `--leading-body-sm` | `1.6` |  |
| `--tracking-body-sm` | `-0.165px` |  |
| `--text-body` | `16px` |  |
| `--leading-body` | `1.5` |  |
| `--leading-snug` | `1.4` |  |
| `--text-14` | `14px` |  |
| `--leading-14` | `1.5` |  |
| `--text-16` | `16px` |  |
| `--leading-16` | `1.5` |  |
| `--text-17` | `17px` |  |
| `--leading-17` | `1.5` |  |
| `--text-body-lg` | `20px` |  |
| `--leading-body-lg` | `1.33` |  |
| `--tracking-body-lg` | `-0.24px` |  |
| `--text-micro` | `11px` |  |
| `--text-label` | `12px` |  |
| `--leading-label` | `1.5` |  |
| `--text-subheading` | `24px` |  |
| `--leading-subheading` | `1.33` |  |
| `--leading-tight` | `1.15` |  |
| `--tracking-subheading` | `-0.288px` |  |
| `--text-heading-sm` | `32px` |  |
| `--leading-heading-sm` | `1.13` |  |
| `--tracking-heading-sm` | `-0.704px` |  |
| `--text-heading` | `48px` |  |
| `--leading-heading` | `1` |  |
| `--tracking-heading` | `-0.704px` |  |
| `--text-heading-lg` | `64px` |  |
| `--leading-heading-lg` | `1` |  |
| `--tracking-heading-lg` | `-1.408px` |  |
| `--text-display` | `72px` |  |
| `--leading-display` | `1` |  |
| `--tracking-display` | `-1.584px` |  |

## 5. Font weights — Vela semantic aliases onto Inter Variable values

| Token | Value | Resolved |
| --- | --- | --- |
| `--font-weight-light` | `300` |  |
| `--font-weight-regular` | `400` |  |
| `--font-weight-medium` | `510` |  |
| `--font-weight-semibold` | `590` |  |

## 6. Spacing — 4px base unit

| Token | Value | Resolved |
| --- | --- | --- |
| `--spacing-unit` | `4px` |  |
| `--spacing-4` | `4px` |  |
| `--spacing-8` | `8px` |  |
| `--spacing-12` | `12px` |  |
| `--spacing-16` | `16px` |  |
| `--spacing-20` | `20px` |  |
| `--spacing-24` | `24px` |  |
| `--spacing-32` | `32px` |  |
| `--spacing-36` | `36px` |  |
| `--spacing-40` | `40px` |  |
| `--spacing-48` | `48px` |  |
| `--spacing-56` | `56px` |  |
| `--spacing-60` | `60px` |  |
| `--spacing-64` | `64px` |  |
| `--spacing-80` | `80px` |  |
| `--spacing-96` | `96px` |  |
| `--spacing-128` | `128px` |  |

## 6a. Spacing — 8px-grid semantic ladder (preferred for layout gaps).
     Each rung aliases an existing 8px-grid primitive so the ladder
     re-tunes automatically if the primitive ever changes.

| Token | Value | Resolved |
| --- | --- | --- |
| `--space-xs` | `var(--spacing-8)` | → `8px` |
| `--space-sm` | `var(--spacing-16)` | → `16px` |
| `--space-md` | `var(--spacing-24)` | → `24px` |
| `--space-lg` | `var(--spacing-32)` | → `32px` |
| `--space-xl` | `var(--spacing-48)` | → `48px` |
| `--space-2xl` | `var(--spacing-64)` | → `64px` |
| `--space-3xl` | `var(--spacing-96)` | → `96px` |

## 7. Layout

| Token | Value | Resolved |
| --- | --- | --- |
| `--page-max-width` | `1200px` |  |
| `--section-gap` | `96px` |  |
| `--card-padding` | `24px` |  |
| `--element-gap` | `8px` |  |

## 8. Border radius — primitives

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

## 9. Shadows

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

## 10. Feedback accents and focus ring

| Token | Value | Resolved |
| --- | --- | --- |
| `--feedback-accent` | `var(--color-acid-lime)` | → `#e4f222` |
| `--feedback-accent-loading` | `var(--color-acid-lime)` | → `#e4f222` |
| `--feedback-accent-success` | `var(--color-pulse-green)` | → `#27a644` |
| `--feedback-accent-error` | `var(--color-coral-red)` | → `#eb5757` |
| `--feedback-accent-info` | `var(--color-signal-teal)` | → `#02b8cc` |
| `--feedback-accent-empty` | `var(--color-smoke)` | → `#383b3f` |
| `--focus-ring-color` | `var(--color-acid-lime)` | → `#e4f222` |

## 11. Motion vocabulary

| Token | Value | Resolved |
| --- | --- | --- |
| `--duration-fast` | `120ms` |  |
| `--duration-base` | `200ms` |  |
| `--duration-slow` | `320ms` |  |
| `--ease-out` | `cubic-bezier(0.2, 0, 0, 1)` |  |

## 12. Font features — Inter Variable OT features for default text

| Token | Value | Resolved |
| --- | --- | --- |
| `--font-feature-settings-default` | `"cv01", "ss03", "zero", "calt"` |  |

## 13. Card primitives — shared by .panel-primary, .dashboard-card,
     .metric-card, and similar surfaces. Aliases onto existing primitives;
     consumer migration is the follow-up `design-system-component-polish`.

| Token | Value | Resolved |
| --- | --- | --- |
| `--card-bg` | `var(--surface-obsidian)` | → `#161718` |
| `--card-border-color` | `rgba(255, 255, 255, 0.06)` |  |
| `--card-padding-x` | `var(--spacing-24)` | → `24px` |
| `--card-padding-y` | `var(--spacing-20)` | → `20px` |
| `--card-radius` | `var(--radius-cards)` | → `12px` |
| `--card-shadow` | `var(--shadow-subtle-3)` | → `rgba(0, 0, 0, 0.01) 0px 5px 2px 0px, rgba(0, 0, 0, 0.04) 0px 3px 2px 0px, rgba(0, 0, 0, 0.07) 0px 1px 1px 0px, rgba(0, 0, 0, 0.08) 0px 0px 1px 0px` |
| `--card-gap` | `var(--element-gap)` | → `8px` |
