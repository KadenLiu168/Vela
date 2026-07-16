## Context

`AppShell` is the shared chrome for every web route. It currently renders `Vela Research` as `<h1>` in the header and places the routed page content inside `<main>`. Each route already renders its own page identity as `<h1>` inside `<main>`, so the rendered page has two top-level headings.

The existing `web-frontend-app` spec permits the AppShell header `<h1>`, but that contract does not match the desired accessibility outcome: the global brand is site chrome, while the routed page title is the document-level identity.

## Goals / Non-Goals

**Goals:**

- Preserve the visual appearance of the AppShell brand.
- Make the AppShell brand non-heading text so it does not compete with the page `<h1>`.
- Keep each routed page's existing `<h1>` as the single page identity heading.
- Replace the structural `.app-header h1` selector with a dedicated class for brand-title styling.

**Non-Goals:**

- Rename page titles or alter page layout.
- Change navigation behavior, routing, API display, or command palette wiring.
- Introduce new typography tokens or broader design-system changes.
- Rework all heading levels across panels and subsections.

## Decisions

1. **Use `<p className="app-brand-title">Vela Research</p>` for the brand.**
   - Rationale: the brand is visible text in the banner, not a section heading. A paragraph preserves readable text semantics without adding a heading to the document outline.
   - Alternative considered: change the brand to `<h2>` or another heading level. Rejected because it still treats site chrome as document structure.
   - Alternative considered: use a plain `<span>`. Rejected because the brand is a standalone text block grouped with API metadata; `<p>` communicates standalone textual content while still avoiding heading semantics.

2. **Move the brand typography rule from `.app-header h1` to `.app-brand-title`.**
   - Rationale: style should target the component role, not a semantic tag. This avoids reintroducing heading coupling if the header later contains another heading.
   - Alternative considered: keep `.app-header h1` and only change JSX. Rejected because the selector would become dead code and keep the old semantic coupling in place.

3. **Modify the existing `web-frontend-app` heading requirement instead of adding a new capability.**
   - Rationale: this is a correction to the existing AppShell/page heading contract, not a new feature area.

## Risks / Trade-offs

- **Risk: snapshot or DOM tests that expect the header `<h1>` fail.** → Update tests to assert the brand class/text and the single page `<h1>` outcome instead.
- **Risk: visual regression from default paragraph margins.** → The `.app-brand-title` rule must carry `margin: 0` and the existing font/color declarations.
- **Trade-off: the brand is no longer discoverable as a heading by assistive technologies.** → This is intentional; the page title should be the heading navigation target, while the brand remains banner text.
