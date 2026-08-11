import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status
  });
}

/** Minimal fetch stub for the declared route map. */
function stubDeclaredRouteApis(requests: string[] = []) {
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    requests.push(url);
    if (url === "/api/dashboard") {
      return Promise.reject(new Error("route test does not provide dashboard data"));
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

it.each([
  ["/", "Dashboard"],
  ["/signals", "Signals"],
  ["/backtests", "Backtests"],
  ["/walk-forwards", "Walk-forward History"]
])("declares the list route %s", async (route, heading) => {
  window.history.pushState({}, "", route);
  stubDeclaredRouteApis();

  render(<App />);

  expect(await screen.findByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
});

it.each([
  ["/signals/42", "Signal Detail"],
  ["/backtests/8", "Backtest Detail"],
  ["/walk-forwards/9", "Walk-forward #9"],
  ["/etfs/1", "ETF Detail"]
])("declares the detail route %s", async (route, heading) => {
  window.history.pushState({}, "", route);
  const fetchMock = vi.fn((input: RequestInfo | URL) =>
    Promise.reject(new Error(`Unexpected request: ${String(input)}`))
  );
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
});

it("renders through browser Back and Forward between declared paths", async () => {
  window.history.pushState({}, "", "/");
  stubDeclaredRouteApis();

  render(<App />);
  expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("link", { name: "Signals" }));
  expect(await screen.findByRole("heading", { name: "Signals" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("link", { name: "Backtests" }));
  expect(await screen.findByRole("heading", { name: "Backtests" })).toBeInTheDocument();

  window.history.back();
  expect(await screen.findByRole("heading", { name: "Signals" })).toBeInTheDocument();

  window.history.forward();
  expect(await screen.findByRole("heading", { name: "Backtests" })).toBeInTheDocument();
});

it.each(["/signals/abc", "/backtests/abc", "/walk-forwards/abc", "/etfs/abc"])(
  "rejects the malformed detail identifier %s before API access",
  async (route) => {
    window.history.pushState({}, "", route);
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      return Promise.reject(new Error(`Unexpected request: ${String(input)}`));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    expect(await screen.findByRole("heading", { level: 1, name: "Page not found" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  }
);

it("renders the explicit not-found page for an unmatched path instead of Dashboard", async () => {
  window.history.pushState({}, "", "/foo");
  stubDeclaredRouteApis();

  render(<App />);

  expect(await screen.findByRole("heading", { level: 1, name: "Page not found" })).toBeInTheDocument();
  expect(screen.queryByRole("heading", { name: "Dashboard" })).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Go to Dashboard" })).toHaveAttribute("href", "/");
});

it("keeps the not-found page inside the persistent AppShell", async () => {
  window.history.pushState({}, "", "/foo");
  stubDeclaredRouteApis();

  render(<App />);

  expect(await screen.findByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "Research navigation" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Signals" })).toBeVisible();
});

it("returns to Dashboard through the not-found link", async () => {
  window.history.pushState({}, "", "/foo");
  stubDeclaredRouteApis();

  render(<App />);

  fireEvent.click(await screen.findByRole("link", { name: "Go to Dashboard" }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  });
  expect(screen.queryByRole("heading", { name: "Page not found" })).not.toBeInTheDocument();
});
