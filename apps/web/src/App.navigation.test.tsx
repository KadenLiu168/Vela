import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import App from "./App";

const scrollToMock = vi.fn();

beforeEach(() => {
  Object.defineProperty(window, "scrollTo", {
    configurable: true,
    value: scrollToMock,
    writable: true
  });
});

afterEach(() => {
  window.history.pushState({}, "", "/");
  scrollToMock.mockClear();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

/** The application is mounted under StrictMode in `main.tsx`, so these tests
 *  mount it the same way: a transition effect that is not idempotent passes
 *  without StrictMode and fails in the real app. */
function renderApp() {
  return render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status
  });
}

/** fetch stub for every declared list route; detail routes are unused here. */
function stubListApis() {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/dashboard") {
      return Promise.reject(new Error("navigation test does not provide dashboard data"));
    }
    if (url === "/api/strategy-signals?limit=20&offset=0") {
      return Promise.resolve(jsonResponse({ signals: [] }));
    }
    if (url === "/api/backtests?limit=10&offset=0") {
      return Promise.resolve(jsonResponse({ runs: [] }));
    }
    if (url === "/api/walk-forwards?limit=10&offset=0") {
      return Promise.resolve(jsonResponse({ runs: [], total: 0, limit: 10, offset: 0 }));
    }
    return Promise.reject(new Error(`Unexpected request: ${url}`));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

it("does not move focus on the initial document load", async () => {
  stubListApis();

  renderApp();

  await screen.findByRole("heading", { level: 1, name: "Dashboard" });
  expect(document.activeElement).toBe(document.body);
  expect(scrollToMock).not.toHaveBeenCalled();
});

it("resets the reading position and focuses the destination heading when navigating", async () => {
  stubListApis();
  renderApp();
  await screen.findByRole("heading", { level: 1, name: "Dashboard" });

  fireEvent.click(screen.getByRole("link", { name: "Signals" }));

  const heading = await screen.findByRole("heading", { level: 1, name: "Signals" });
  await waitFor(() => expect(document.activeElement).toBe(heading));
  expect(scrollToMock).toHaveBeenCalledWith(0, 0);
});

it("focuses the destination heading after a lazy route module resolves", async () => {
  stubListApis();
  renderApp();
  await screen.findByRole("heading", { level: 1, name: "Dashboard" });

  // Backtests is a lazy route: the loading fallback renders before the page
  // module resolves, so the destination <h1> does not exist until later.
  fireEvent.click(screen.getByRole("link", { name: "Backtests" }));
  expect(document.querySelector("main h1")).not.toBeInTheDocument();

  const heading = await screen.findByRole("heading", { level: 1, name: "Backtests" });
  await waitFor(() => expect(document.activeElement).toBe(heading));
});

it("moves focus again on a second navigation", async () => {
  stubListApis();
  renderApp();
  await screen.findByRole("heading", { level: 1, name: "Dashboard" });

  fireEvent.click(screen.getByRole("link", { name: "Signals" }));
  await screen.findByRole("heading", { level: 1, name: "Signals" });

  fireEvent.click(screen.getByRole("link", { name: "Backtests" }));

  const heading = await screen.findByRole("heading", { level: 1, name: "Backtests" });
  await waitFor(() => expect(document.activeElement).toBe(heading));
});

it("keeps the focused page heading out of the sequential tab order", async () => {
  stubListApis();
  renderApp();
  await screen.findByRole("heading", { level: 1, name: "Dashboard" });

  fireEvent.click(screen.getByRole("link", { name: "Signals" }));

  const heading = await screen.findByRole("heading", { level: 1, name: "Signals" });
  expect(heading).toHaveAttribute("tabindex", "-1");
});

it("titles each declared route and does not retain the previous title", async () => {
  stubListApis();
  renderApp();

  await screen.findByRole("heading", { level: 1, name: "Dashboard" });
  expect(document.title).toBe("Dashboard · Vela Research");

  fireEvent.click(screen.getByRole("link", { name: "Signals" }));
  await screen.findByRole("heading", { level: 1, name: "Signals" });
  expect(document.title).toBe("Signals · Vela Research");

  fireEvent.click(screen.getByRole("link", { name: "Walk-forwards" }));
  await screen.findByRole("heading", { level: 1, name: "Walk-forward History" });
  expect(document.title).toBe("Walk-forward History · Vela Research");
});

it("titles the unmatched route", async () => {
  window.history.pushState({}, "", "/no-such-page");
  stubListApis();

  renderApp();

  await screen.findByRole("heading", { level: 1, name: "Page not found" });
  expect(document.title).toBe("Page not found · Vela Research");
});

it("titles a detail route with its entity identifier", async () => {
  window.history.pushState({}, "", "/etfs/1234");
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.reject(new Error("detail data is irrelevant to the title")))
  );

  renderApp();

  const heading = await screen.findByRole("heading", { level: 1, name: "ETF Detail" });
  expect(document.title).toBe("ETF Detail #1234 · Vela Research");
  expect(document.title.startsWith(heading.textContent ?? "")).toBe(true);
});

it("renders the skip link as the first focusable element and moves focus into main", async () => {
  stubListApis();
  renderApp();
  await screen.findByRole("heading", { level: 1, name: "Dashboard" });

  const skipLink = screen.getByRole("link", { name: "Skip to main content" });
  const main = document.querySelector("main");
  expect(main).not.toBeNull();
  expect(skipLink).toHaveAttribute("href", "#main-content");
  expect(main).toHaveAttribute("id", "main-content");
  expect(main).toHaveAttribute("tabindex", "-1");
  expect(document.querySelectorAll<HTMLElement>("a[href], button, input, select, textarea")[0]).toBe(
    skipLink
  );

  skipLink.focus();
  fireEvent.click(skipLink);

  expect(document.activeElement).toBe(main);
});
