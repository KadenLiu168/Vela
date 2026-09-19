import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { ApiClientError } from "../api/client";
import { ReadFailure } from "./ReadFailure";

it("states what failed and why in user-facing terms", () => {
  render(
    <ReadFailure
      error={new ApiClientError("offline", { kind: "network" })}
      label="Signal history"
      onRetry={() => undefined}
    />
  );

  const alert = screen.getByRole("alert");
  expect(alert).toHaveTextContent("Signal history could not be loaded.");
  expect(alert).toHaveTextContent("The local API could not be reached.");
  expect(alert).not.toHaveTextContent(/network/i);
});

it("reports an error response with its status code", () => {
  render(
    <ReadFailure
      error={new ApiClientError("boom", { kind: "http", status: 503, category: "unexpected" })}
      label="Backtest history"
      onRetry={() => undefined}
    />
  );

  expect(screen.getByRole("alert")).toHaveTextContent("The API returned an error response (503).");
});

it("offers a retry control that declares its button variant", () => {
  const onRetry = vi.fn();
  render(
    <ReadFailure
      error={new ApiClientError("offline", { kind: "network" })}
      label="Signal history"
      onRetry={onRetry}
    />
  );

  const retry = screen.getByRole("button", { name: "Retry" });
  expect(retry).toHaveClass("button-secondary");

  fireEvent.click(retry);
  expect(onRetry).toHaveBeenCalledTimes(1);
});
