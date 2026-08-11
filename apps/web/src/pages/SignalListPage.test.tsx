import { fireEvent, screen, waitFor } from "@testing-library/react";
import { useLocation } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { listStrategySignals } from "../api/client";
import { renderWithRouter } from "../test/renderWithRouter";
import { SignalListPage } from "./SignalListPage";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, listStrategySignals: vi.fn() };
});

const listSignalsMock = vi.mocked(listStrategySignals);

const manualSignal = {
  backtest_run_id: null,
  config_version: "v1",
  generated_at: "2026-07-20T09:30:00",
  is_fallback: false,
  position_count: 1,
  result: "rebalance",
  signal_date: "2026-07-20",
  signal_id: 7,
  source: "manual" as const
};

function LocationProbe() {
  const location = useLocation();
  return (
    <span data-testid="location-probe">
      {location.pathname}
      {location.search}
      {location.hash}
    </span>
  );
}

function renderSignals(route: string) {
  return renderWithRouter(
    <>
      <SignalListPage />
      <LocationProbe />
    </>,
    route
  );
}

afterEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, "", "/signals");
});

it("initializes a valid source filter from the URL and requests it", async () => {
  listSignalsMock.mockResolvedValue({ signals: [] });

  renderSignals("/signals?source=scheduled");

  await waitFor(() => expect(listSignalsMock).toHaveBeenCalledWith(20, 0, "scheduled"));
  expect(screen.getByRole("button", { name: "Scheduled" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByText("No successful signals are available for Scheduled.")).toBeInTheDocument();
});

it.each(["unknown", "", "null"])("normalizes the %j source URL value to All", async (invalidSource) => {
  listSignalsMock.mockResolvedValue({ signals: [] });

  renderSignals(`/signals?keep=yes&source=${invalidSource}#notes`);

  await waitFor(() => expect(listSignalsMock).toHaveBeenCalledWith(20, 0, undefined));
  expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  await waitFor(() => {
    expect(screen.getByTestId("location-probe")).toHaveTextContent("/signals?keep=yes#notes");
  });
});

it("switches source, resets offset, and preserves unrelated URL state when All is selected", async () => {
  listSignalsMock.mockResolvedValue({ signals: [] });
  renderSignals("/signals?keep=yes&source=backtest#notes");

  await waitFor(() => expect(listSignalsMock).toHaveBeenCalledWith(20, 0, "backtest"));
  fireEvent.click(screen.getByRole("button", { name: "Manual" }));
  await waitFor(() => expect(listSignalsMock).toHaveBeenLastCalledWith(20, 0, "manual"));
  expect(screen.getByTestId("location-probe")).toHaveTextContent("/signals?keep=yes&source=manual#notes");

  fireEvent.click(screen.getByRole("button", { name: "All" }));
  await waitFor(() => expect(listSignalsMock).toHaveBeenLastCalledWith(20, 0, undefined));
  expect(screen.getByTestId("location-probe")).toHaveTextContent("/signals?keep=yes#notes");
});

it("resets an advanced page to offset zero when the source changes", async () => {
  listSignalsMock.mockResolvedValue({
    signals: Array.from({ length: 20 }, (_, index) => ({ ...manualSignal, signal_id: index + 1 }))
  });
  renderSignals("/signals");

  fireEvent.click(await screen.findByRole("button", { name: "Next" }));
  await waitFor(() => expect(listSignalsMock).toHaveBeenLastCalledWith(20, 20, undefined));
  fireEvent.click(screen.getByRole("button", { name: "Scheduled" }));

  await waitFor(() => expect(listSignalsMock).toHaveBeenLastCalledWith(20, 0, "scheduled"));
});

it("normalizes invalid URL source values and prevents stale source responses from replacing current data", async () => {
  let resolveBacktest!: (value: { signals: [] }) => void;
  listSignalsMock
    .mockResolvedValueOnce({ signals: [] })
    .mockImplementationOnce(() => new Promise((resolve) => { resolveBacktest = resolve; }))
    .mockResolvedValueOnce({ signals: [] });
  renderSignals("/signals?source=null&keep=yes#notes");

  await waitFor(() => expect(listSignalsMock).toHaveBeenCalledWith(20, 0, undefined));
  await waitFor(() => {
    expect(screen.getByTestId("location-probe")).toHaveTextContent("/signals?keep=yes#notes");
  });

  fireEvent.click(screen.getByRole("button", { name: "Backtest" }));
  fireEvent.click(screen.getByRole("button", { name: "Legacy" }));
  resolveBacktest({ signals: [] });

  await waitFor(() => expect(screen.getByRole("button", { name: "Legacy" })).toHaveAttribute("aria-pressed", "true"));
  expect(screen.getByText("No successful signals are available for Legacy.")).toBeInTheDocument();
});

it("does not show the previous source rows while the next source is loading", async () => {
  let resolveBacktest!: (value: { signals: [] }) => void;
  listSignalsMock
    .mockResolvedValueOnce({ signals: [manualSignal] })
    .mockImplementationOnce(() => new Promise((resolve) => { resolveBacktest = resolve; }));
  renderSignals("/signals");

  await screen.findByRole("link", { name: "#7" });
  fireEvent.click(screen.getByRole("button", { name: "Backtest" }));

  expect(screen.queryByRole("link", { name: "#7" })).not.toBeInTheDocument();
  expect(screen.getByText("Loading signal history.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Backtest" })).toHaveAttribute("aria-pressed", "true");

  resolveBacktest({ signals: [] });
  await screen.findByText("No successful signals are available for Backtest.");
});
