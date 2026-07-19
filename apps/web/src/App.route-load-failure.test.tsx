import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

vi.mock("./pages/SignalListPage", () => Promise.reject(new Error("route chunk unavailable")));

const { default: App } = await import("./App");

afterEach(() => {
  window.history.pushState({}, "", "/");
  vi.restoreAllMocks();
});

it("shows a reload action for a failed route chunk and recovers through navigation", async () => {
  window.history.pushState({}, "", "/signals");
  vi.spyOn(console, "error").mockImplementation(() => undefined);

  render(<App />);

  expect(await screen.findByText("Unable to load this page.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Reload page" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Dashboard" })).toBeVisible();

  fireEvent.click(screen.getByRole("link", { name: "Dashboard" }));

  expect(await screen.findByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
  expect(screen.queryByText("Unable to load this page.")).not.toBeInTheDocument();
});
