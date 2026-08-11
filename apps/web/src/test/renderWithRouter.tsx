import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

/**
 * Renders a component that depends on Router context (Link, useNavigate,
 * useParams, useSearchParams) inside a MemoryRouter.
 *
 * The default initial entry is derived from the current window location so
 * existing tests that pre-seed `window.history.pushState` keep working.
 */
export function renderWithRouter(
  ui: ReactElement,
  initialEntry: string = window.location.pathname + window.location.search + window.location.hash
): RenderResult {
  return render(<MemoryRouter initialEntries={[initialEntry]}>{ui}</MemoryRouter>);
}
