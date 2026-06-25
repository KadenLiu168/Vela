import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.unstubAllGlobals();
});

it("renders the web app skeleton", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: "Vela Web" })).toBeInTheDocument();
  expect(screen.getByText("Frontend skeleton ready")).toBeInTheDocument();
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
