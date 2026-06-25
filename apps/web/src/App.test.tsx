import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
});

it("renders the workflow dashboard on the default route", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: "Workflow Dashboard" })).toBeInTheDocument();
  expect(screen.getByText("Local research workflow")).toBeInTheDocument();
});

it("loads API health through the shared client", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ status: "healthy" }), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  render(<App />);

  expect(await screen.findByText("API status: healthy")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/health", undefined);
});

it("renders the signal detail placeholder route", () => {
  window.history.pushState({}, "", "/signals/demo-signal");

  render(<App />);

  expect(screen.getByRole("heading", { name: "Signal Detail" })).toBeInTheDocument();
  expect(screen.getByText("Signal ID: demo-signal")).toBeInTheDocument();
});

it("renders the backtest detail placeholder route", () => {
  window.history.pushState({}, "", "/backtests/demo-backtest");

  render(<App />);

  expect(screen.getByRole("heading", { name: "Backtest Detail" })).toBeInTheDocument();
  expect(screen.getByText("Backtest ID: demo-backtest")).toBeInTheDocument();
});

it("exposes local research navigation without production account entry points", () => {
  render(<App />);

  expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/");
  expect(screen.getByRole("link", { name: "Signal Detail" })).toHaveAttribute(
    "href",
    "/signals/demo-signal"
  );
  expect(screen.getByRole("link", { name: "Backtest Detail" })).toHaveAttribute(
    "href",
    "/backtests/demo-backtest"
  );

  expect(screen.queryByText(/login|sign up|account|team|deploy|production/i)).not.toBeInTheDocument();
});
