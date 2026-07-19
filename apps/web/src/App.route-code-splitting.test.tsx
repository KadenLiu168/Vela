import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.unstubAllGlobals();
});

it("keeps AppShell navigation visible while a non-default route module loads", () => {
  window.history.pushState({}, "", "/signals");

  render(<App />);

  expect(screen.getByRole("link", { name: "Dashboard" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Signals" })).toBeVisible();
  expect(screen.getByRole("status", { name: "Loading page" })).toBeInTheDocument();
  expect(screen.getAllByRole("presentation", { hidden: true }).length).toBeGreaterThan(0);
});
