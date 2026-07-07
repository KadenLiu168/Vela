## 1. Skeleton component

- [ ] 1.1 Create `apps/web/src/components/Skeleton.tsx` exporting a
      `Skeleton` function component with the following API:
      ```ts
      type SkeletonProps = {
        as?: "inline" | "block";
        variant?: "text" | "circle";
        width?: string | number;
        height?: string | number;
        diameter?: string | number;
        className?: string;
      };
      ```
      - Default `as="inline"`, `variant="text"`, `width="100%"`,
        `height="0.75em"`.
      - `variant="circle"` overrides width/height with `diameter`
        and applies `border-radius: 9999px` via a `.skeleton-circle`
        class.
      - The rendered element gets `className="skeleton"` plus
        optional `skeleton-pulse` and `skeleton-circle`.
- [ ] 1.2 In `apps/web/src/styles.css`, add the `.skeleton`,
      `.skeleton-pulse`, `.skeleton-circle`, `@keyframes
      skeleton-pulse`, and `@media (prefers-reduced-motion:
      reduce) { .skeleton-pulse { animation: none; opacity: 0.55 } }`
      rules. Place them after the existing
      `.feedback-message-error` rule so the state-surface family
      lives together.

## 2. ErrorBoundary component

- [ ] 2.1 Create `apps/web/src/components/ErrorBoundary.tsx`
      exporting a React class component named `ErrorBoundary`
      with props:
      ```ts
      type ErrorBoundaryProps = {
        children: ReactNode;
        fallback?: ReactNode;
      };
      ```
      Internal state: `hasError: boolean`.
      `componentDidCatch(error, info)` sets `hasError = true`
      and logs the error to `console.error` (no Sentry / no
      external logger in this change).
      `getDerivedStateFromError` returns `{ hasError: true }`.
      `render()` returns `children` when `hasError` is false;
      returns `fallback ?? <FeedbackMessage variant="error">…</FeedbackMessage>`
      when `hasError` is true.
- [ ] 2.2 In `apps/web/src/styles.css`, add a `.error-boundary`
      rule (margin / padding wrapper) immediately after the new
      `.skeleton-circle` rule.

## 3. Barrel export

- [ ] 3.1 Create `apps/web/src/components/index.ts` that
      re-exports `EmptyState`, `FeedbackMessage`,
      `ErrorBoundary` (from this change), and `Skeleton` (from
      this change). Use named re-exports, not default.
- [ ] 3.2 Do NOT modify or delete
      `apps/web/src/components/FeedbackMessage.tsx`. Existing
      direct-path imports continue to work; the barrel is the
      canonical import path for new code.

## 4. Import migration

- [ ] 4.1 In `apps/web/src/pages/DashboardPage.tsx`, change
      `import { EmptyState, FeedbackMessage } from "../components/FeedbackMessage";`
      to `import { EmptyState, FeedbackMessage } from "../components";`.
      No other change in the file.
- [ ] 4.2 In `apps/web/src/pages/SignalDetailPage.tsx`, change
      the same import line to point at `"../components"`.
- [ ] 4.3 In `apps/web/src/pages/BacktestDetailPage.tsx`, change
      the same import line to point at `"../components"`.
- [ ] 4.4 Run `npm --prefix apps/web run typecheck` and confirm
      the import migration does not introduce any TS error.

## 5. ErrorBoundary wrap at App root

- [ ] 5.1 In `apps/web/src/App.tsx`, add
      `import { ErrorBoundary } from "./components";` to the
      existing imports block.
- [ ] 5.2 Wrap the `renderRoute(path)` call inside the
      `AppShell` children in `<ErrorBoundary>...</ErrorBoundary>`.
      The boundary's fallback is the default
      `<FeedbackMessage variant="error">Something went wrong
      while rendering this page.</FeedbackMessage>`.

## 6. Spec delta

- [ ] 6.1 Append the new Requirement "State component set is
      exported from the components barrel" and its 4 Scenarios
      into `openspec/specs/design-system/spec.md` at archive
      time. The delta file
      `openspec/changes/design-system-state-components/specs/design-system/spec.md`
      is the source of truth; `openspec archive` merges it
      under the `## ADDED Requirements` heading.

## 7. Validation

- [ ] 7.1 Run `openspec validate design-system-state-components`
      and confirm exit 0.
- [ ] 7.2 Run `openspec validate design-system` (post-archive)
      and confirm the merged capability still validates.
- [ ] 7.3 Run `npm --prefix apps/web run typecheck` — exit 0.
      Specifically confirm:
      - `SkeletonProps` type checks
      - `ErrorBoundary` class component type checks
      - No `any` leak
- [ ] 7.4 Run `npm --prefix apps/web run lint` — exit 0.
- [ ] 7.5 Run `npm --prefix apps/web run test` — exit 0.
      Expected: 71 passed / 7 skipped (unchanged from
      baseline). The barrel re-exports preserve all existing
      test assertions; the new components are not yet
      consumed by tests.
- [ ] 7.6 Run `npm --prefix apps/web run build` — exit 0;
      CSS bundle size delta expected ~ +0.2 KB (the new
      `.skeleton`, `.skeleton-pulse`, `.skeleton-circle`,
      `@keyframes`, reduced-motion override, and
      `.error-boundary` rules).
- [ ] 7.7 Run `uv run pytest -q` from the repo root — 417
      passed (no backend changes in this change).
- [ ] 7.8 Eyeball the dev server with a deliberate render
      error (e.g. add a `throw new Error("test")` to one
      page, refresh, then revert) and confirm the
      `<ErrorBoundary>` fallback shows the canonical
      FeedbackMessage error surface in the AppShell `<main>`.
      Revert the deliberate error before commit.

## 8. Commit and push

- [ ] 8.1 `git status` shows only the new component files,
      the modified CSS, the modified 3 page imports, the
      modified App.tsx, the merged `design-system/spec.md`,
      and the contents of
      `openspec/changes/design-system-state-components/`.
- [ ] 8.2 `git add` those files explicitly (no `git add .`).
- [ ] 8.3 `git commit -m "feat(design-system): add state component set (F-107)"`
      (Conventional Commits, scoped to design-system, references
      F-107 in the body).
- [ ] 8.4 `git push origin main`.
