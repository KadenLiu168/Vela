import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { ApiClientError, type BacktestListItem, listBacktests } from "../api/client";
import { renderWithRouter } from "../test/renderWithRouter";
import { BacktestListPage } from "./BacktestListPage";

function RouterWrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, listBacktests: vi.fn() };
});

const listMock = vi.mocked(listBacktests);

afterEach(() => vi.clearAllMocks());

const item = (overrides: Partial<BacktestListItem> = {}): BacktestListItem => ({
  run_id: 7,
  strategy_id: "s",
  config_version: "v1",
  start_date: "2026-01-01",
  end_date: "2026-01-02",
  status: "success",
  started_at: "2026-01-01T00:00:00",
  finished_at: "2026-01-01T00:00:01",
  total_return: "0.12",
  annualized_return: "0.11",
  max_drawdown: "-0.09",
  volatility: "0.15",
  sharpe_ratio: "1.5",
  ...overrides
});

it("shows Total return, CAGR (calendar-time), and Sharpe (daily returns, 252D) columns from existing fields", async () => {
  listMock.mockResolvedValue({ runs: [item()] });
  render(<BacktestListPage />, { wrapper: RouterWrapper });

  await screen.findByRole("link", { name: "#7" });
  expect(screen.getByRole("columnheader", { name: "Total return" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "CAGR (calendar-time)" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Sharpe (daily returns, 252D)" })).toBeInTheDocument();

  const row = screen.getByRole("row", { name: /#7/ });
  expect(within(row).getByText("12.00%")).toBeInTheDocument();
  expect(within(row).getByText("11.00%")).toBeInTheDocument();
  expect(within(row).getByText("1.50")).toBeInTheDocument();
});

it("renders null and legacy rows through the existing unavailable formatting", async () => {
  listMock.mockResolvedValue({
    runs: [
      item({ run_id: 1, total_return: null, annualized_return: null, sharpe_ratio: null, status: "failed" }),
      item({ run_id: 2 })
    ]
  });
  render(<BacktestListPage />, { wrapper: RouterWrapper });

  await screen.findByRole("link", { name: "#1" });
  const legacyRow = screen.getByRole("row", { name: /#1/ });
  expect(within(legacyRow).getAllByText("n/a").length).toBe(3);
  expect(within(legacyRow).queryByText("NaN")).not.toBeInTheDocument();

  const populatedRow = screen.getByRole("row", { name: /#2/ });
  expect(within(populatedRow).getByText("12.00%")).toBeInTheDocument();
});

it("keeps links, run metadata, and pagination intact", async () => {
  listMock.mockResolvedValue({ runs: Array.from({ length: 10 }, (_, index) => item({ run_id: 10 + index })) });
  render(<BacktestListPage />, { wrapper: RouterWrapper });

  const firstLink = await screen.findByRole("link", { name: "#10" });
  expect(firstLink).toHaveAttribute("href", "/backtests/10");
  expect(screen.getByRole("columnheader", { name: "Run" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Date range" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Status" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Started at" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Next" })).toBeInTheDocument();
});

it("renders loading, error, and empty states", async () => {
  listMock.mockImplementation(() => new Promise(() => undefined));
  render(<BacktestListPage />, { wrapper: RouterWrapper });
  expect(screen.getByText("Loading backtest history.")).toBeInTheDocument();

  listMock.mockRejectedValue(new ApiClientError("offline", { kind: "network" }));
  render(<BacktestListPage />, { wrapper: RouterWrapper });
  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("Backtest history could not be loaded.");
  expect(alert).toHaveTextContent("The local API could not be reached");
  expect(alert).not.toHaveTextContent(/network/);

  listMock.mockResolvedValue({ runs: [] });
  render(<BacktestListPage />, { wrapper: RouterWrapper });
  expect(
    await screen.findByText(/No local backtest run exists yet/)
  ).toBeInTheDocument();
});

it("reports an error response with its status code and recovers through Retry", async () => {
  listMock.mockRejectedValueOnce(
    new ApiClientError("boom", { kind: "http", status: 503, category: "unexpected" })
  );
  listMock.mockResolvedValueOnce({ runs: [item({ run_id: 7 })] });
  render(<BacktestListPage />, { wrapper: RouterWrapper });

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("The API returned an error response (503).");

  fireEvent.click(screen.getByRole("button", { name: "Retry" }));

  await screen.findByRole("link", { name: "#7" });
  expect(listMock).toHaveBeenLastCalledWith(10, 0);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it("requests the next page through pagination", async () => {
  listMock.mockResolvedValue({
    runs: Array.from({ length: 10 }, (_, index) => item({ run_id: 30 + index }))
  });
  render(<BacktestListPage />, { wrapper: RouterWrapper });

  await screen.findByRole("link", { name: "#30" });
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  await waitFor(() => expect(listMock).toHaveBeenLastCalledWith(10, 10));
  expect(screen.getByRole("button", { name: "Previous" })).toBeInTheDocument();
});

it("keeps metric columns inside a labeled keyboard-scrollable region without page overflow", async () => {
  Object.defineProperty(window, "innerWidth", { value: 390, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: 844, configurable: true, writable: true });
  listMock.mockResolvedValue({ runs: [item()] });
  render(<BacktestListPage />, { wrapper: RouterWrapper });

  await screen.findByRole("link", { name: "#7" });
  const region = screen.getByLabelText("Backtest runs table");
  expect(region).toHaveAttribute("tabindex", "0");
  expect(screen.getByRole("columnheader", { name: "Sharpe (daily returns, 252D)" })).toBeInTheDocument();
  expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(390);
});

function LocationProbe() {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <span data-testid="location-probe">{`${location.pathname}${location.search}${location.hash}`}</span>
      <button onClick={() => navigate(-1)} type="button">
        go back
      </button>
    </>
  );
}

function renderRoutes(initialEntry: string) {
  return renderWithRouter(
    <>
      <Routes>
        <Route element={<BacktestListPage />} path="/backtests" />
        <Route element={<p>detail stub</p>} path="/backtests/:backtestId" />
      </Routes>
      <LocationProbe />
    </>,
    initialEntry
  );
}

it("initializes the list from a valid offset in the URL", async () => {
  listMock.mockResolvedValue({ runs: [item({ run_id: 7 })] });
  renderRoutes("/backtests?offset=20");

  await screen.findByRole("link", { name: "#7" });
  expect(listMock).toHaveBeenCalledWith(10, 20);
  expect(screen.getByRole("button", { name: "Previous" })).not.toBeDisabled();
});

it("writes the offset to the URL while preserving unrelated query parameters and the hash", async () => {
  listMock.mockResolvedValue({
    runs: Array.from({ length: 10 }, (_, index) => item({ run_id: 30 + index }))
  });
  renderRoutes("/backtests?view=compact#runs");

  await screen.findByRole("link", { name: "#30" });
  fireEvent.click(screen.getByRole("button", { name: "Next" }));

  await waitFor(() => expect(listMock).toHaveBeenLastCalledWith(10, 10));
  expect(screen.getByTestId("location-probe")).toHaveTextContent("/backtests?view=compact&offset=10#runs");
});

it("normalizes an invalid offset and loads the first page", async () => {
  listMock.mockResolvedValue({ runs: [item({ run_id: 7 })] });
  renderRoutes("/backtests?offset=abc&view=compact#runs");

  await screen.findByRole("link", { name: "#7" });
  expect(listMock).toHaveBeenCalledWith(10, 0);
  await waitFor(() =>
    expect(screen.getByTestId("location-probe")).toHaveTextContent("/backtests?view=compact#runs")
  );
});

it("restores the list offset when returning from a detail page", async () => {
  listMock.mockResolvedValue({
    runs: Array.from({ length: 10 }, (_, index) => item({ run_id: 30 + index }))
  });
  renderRoutes("/backtests");

  await screen.findByRole("link", { name: "#30" });
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  await waitFor(() => expect(listMock).toHaveBeenLastCalledWith(10, 10));

  fireEvent.click(await screen.findByRole("link", { name: "#30" }));
  await screen.findByText("detail stub");

  fireEvent.click(screen.getByRole("button", { name: "go back" }));

  await screen.findByRole("link", { name: "#30" });
  expect(listMock).toHaveBeenLastCalledWith(10, 10);
});
