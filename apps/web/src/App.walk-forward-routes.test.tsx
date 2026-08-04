import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    status: 200
  });
}

it("loads the Walk-forward route directly and returns to it through active navigation", async () => {
  window.history.pushState({}, "", "/walk-forwards");
  const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
    if (String(input) === "/api/walk-forwards?limit=10&offset=0") {
      return Promise.resolve({
        runs: [],
        total: 0,
        limit: 10,
        offset: 0
      }).then(jsonResponse);
    }
    return Promise.reject(new TypeError("route test does not provide this API"));
  });
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByRole("heading", { name: "Walk-forward History" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Walk-forwards" })).toHaveAttribute(
    "aria-current",
    "page"
  );
  expect(await screen.findByText(/No complete Walk-forward evaluation/)).toBeInTheDocument();

  fireEvent.click(screen.getByRole("link", { name: "Dashboard" }));
  fireEvent.click(screen.getByRole("link", { name: "Walk-forwards" }));
  await waitFor(() => {
    expect(fetchMock.mock.calls.filter(([input]) => String(input) === "/api/walk-forwards?limit=10&offset=0")).toHaveLength(2);
  });
  expect(await screen.findByRole("heading", { name: "Walk-forward History" })).toBeInTheDocument();
});
