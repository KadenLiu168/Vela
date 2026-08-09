## ADDED Requirements

### Requirement: Vertical rhythm between headings and content
Page-level headings and section headings in the web frontend MUST be separated from the content that follows them by design-system spacing tokens. List pages (`page-heading h1`) MUST separate the page title from the first main content element that follows the page heading — whether that element is a `.dashboard-panel`, an empty-state surface (`.empty-state`/`.status-surface`), a feedback message (`.feedback-message`), or a run-trigger control — by `var(--space-xl)` (48px). Detail-page section headings (`.holdings-section h2`) MUST separate the heading from the body content that follows by `var(--spacing-16)` (16px). Layout-gap values for heading-to-content rhythm MUST resolve through the `--space-*` or `--spacing-*` token ladder rather than ad-hoc literals.

#### Scenario: list page title is separated from main content
- **WHEN** a Signals, Backtests, or Walk-forwards list page renders its `page-heading h1` followed by its first main content element (a `.dashboard-panel`, an empty-state surface, a feedback message, or the `.walk-forward-run-trigger` control)
- **THEN** that first content element MUST be placed `var(--space-xl)` (48px) below the heading
- **AND** the spacing MUST be declared via `var(--space-xl)` in `apps/web/src/styles.css`

#### Scenario: detail section heading is separated from body content
- **WHEN** a detail page renders a `.holdings-section h2` heading
- **THEN** the heading MUST use the design-system section heading spec (font-family `var(--font-display)`, font-size `var(--text-subheading)`, font-weight `var(--font-weight-medium)`, letter-spacing `var(--tracking-subheading)`, line-height `var(--leading-subheading)`)
- **AND** its `margin` MUST be `0 0 var(--spacing-16)` so the heading is separated from the following body content by 16px
