import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ApiClientError, getBacktestDetail, listBacktestSignals } from "../api/client";
import { BacktestDetailPage } from "./BacktestDetailPage";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, getBacktestDetail: vi.fn(), listBacktestSignals: vi.fn() };
});

const detailMock = vi.mocked(getBacktestDetail);
const signalsMock = vi.mocked(listBacktestSignals);

const detail = (signalCount: number, runId = 7) => ({
  benchmarks: [],
  equity_curve: [],
  metrics: { annualized_return: null, max_drawdown: null, sharpe_ratio: null, total_return: null, volatility: null },
  run: { config_version: "v1", end_date: "2026-01-02", error_message: null, finished_at: null, parameters_json: null, run_id: runId, start_date: "2026-01-01", started_at: "2026-01-01T00:00:00", status: "success", strategy_id: "s" },
  signal_count: signalCount,
  signal_ids: []
});

afterEach(() => vi.clearAllMocks());

it("renders Overview by default with connected automatically activated tabs", async () => {
  detailMock.mockResolvedValue(detail(1));
  signalsMock.mockResolvedValue({ signals: [] });
  render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  const overview = screen.getByRole("tab", { name: "Overview" });
  const signals = screen.getByRole("tab", { name: "Signals (1)" });
  expect(overview).toHaveAttribute("aria-selected", "true");
  expect(screen.getByRole("tabpanel", { name: "Overview" })).toBeInTheDocument();
  expect(signalsMock).not.toHaveBeenCalled();

  fireEvent.keyDown(overview, { key: "ArrowRight" });
  await waitFor(() => expect(signalsMock).toHaveBeenCalledWith("7", 20, 0));
  expect(signals).toHaveAttribute("aria-selected", "true");
  expect(document.activeElement).toBe(signals);
});

it("renders benchmark metric groups and an accessible three-series legend", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    benchmarks: [
      {
        key: "equal_weight_monthly",
        name: "Equal-weight monthly rebalanced portfolio",
        total_return: "0.1", annualized_return: "0.1", max_drawdown: "-0.1", volatility: "0.1", sharpe_ratio: "1",
        total_return_difference: "0.02", annualized_return_difference: "0.02",
        equity_curve: [{ trade_date: "2026-01-01", net_value: "1" }, { trade_date: "2026-01-02", net_value: "1.1" }]
      },
      {
        key: "csi_300_buy_hold",
        name: "CSI 300 buy-and-hold",
        total_return: "0.08", annualized_return: "0.08", max_drawdown: "-0.08", volatility: "0.08", sharpe_ratio: "0.8",
        total_return_difference: "0.04", annualized_return_difference: "0.04",
        equity_curve: [{ trade_date: "2026-01-01", net_value: "1" }, { trade_date: "2026-01-02", net_value: "1.08" }]
      }
    ],
    equity_curve: [
      { trade_date: "2026-01-01", net_value: "1", cash: "0", market_value: "1", total_assets: "1", positions_json: "[]" },
      { trade_date: "2026-01-02", net_value: "1.12", cash: "0", market_value: "1.12", total_assets: "1.12", positions_json: "[]" }
    ]
  });
  render(<BacktestDetailPage backtestId="7" />);

  await screen.findByRole("heading", { name: "Equal-weight monthly rebalanced portfolio" });
  expect(screen.getByRole("heading", { name: "CSI 300 buy-and-hold" })).toBeInTheDocument();
  const legend = screen.getByRole("list", { name: "Equity curve legend" });
  expect(legend).toHaveTextContent("Strategy");
  expect(legend).toHaveTextContent("Equal-weight monthly rebalanced portfolio");
  expect(legend).toHaveTextContent("CSI 300 buy-and-hold");
  expect(screen.getByTestId("equity-curve-line-strategy")).toBeInTheDocument();
  expect(screen.getByTestId("equity-curve-line-equal_weight_monthly")).toBeInTheDocument();
  expect(screen.getByTestId("equity-curve-line-csi_300_buy_hold")).toBeInTheDocument();
});

it("wraps ArrowLeft and ArrowRight and supports Home and End", async () => {
  detailMock.mockResolvedValue(detail(0));
  render(<BacktestDetailPage backtestId="7" />);

  const overview = await screen.findByRole("tab", { name: "Overview" });
  const signals = screen.getByRole("tab", { name: "Signals (0)" });

  fireEvent.keyDown(overview, { key: "ArrowLeft" });
  expect(document.activeElement).toBe(signals);
  expect(signals).toHaveAttribute("aria-selected", "true");

  fireEvent.keyDown(signals, { key: "ArrowRight" });
  expect(document.activeElement).toBe(overview);
  expect(overview).toHaveAttribute("aria-selected", "true");

  fireEvent.keyDown(overview, { key: "End" });
  expect(document.activeElement).toBe(signals);
  fireEvent.keyDown(signals, { key: "Home" });
  expect(document.activeElement).toBe(overview);
});

it("does not request zero-count signals and renders the explicit empty state", async () => {
  detailMock.mockResolvedValue(detail(0));
  render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (0)" }));
  expect(signalsMock).not.toHaveBeenCalled();
  expect(screen.getByText("No signals are linked to this backtest.")).toBeInTheDocument();
});

it("renders the signals table and uses signal_count for an exact final-page boundary", async () => {
  detailMock.mockResolvedValue(detail(20));
  signalsMock.mockResolvedValue({ signals: Array.from({ length: 20 }, (_, index) => ({ backtest_run_id: 7, result: "rebalance", signal_date: "2026-01-02", signal_id: 80 + index })) });
  render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (20)" }));
  await screen.findByRole("link", { name: "Signal #99" });
  expect(screen.getByRole("columnheader", { name: "Signal #" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Signal date" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Result" })).toBeInTheDocument();
  expect(screen.getByRole("columnheader", { name: "Action" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Signal #99" })).toHaveAttribute("href", "/signals/99");
  expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
});

it("loads signals lazily, shows request feedback, and reuses the loaded page after a tab switch", async () => {
  let resolveSignals!: (value: { signals: [] }) => void;
  detailMock.mockResolvedValue(detail(1));
  signalsMock.mockImplementation(() => new Promise((resolve) => { resolveSignals = resolve; }));
  render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  expect(signalsMock).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("tab", { name: "Signals (1)" }));
  expect(screen.getByText("Loading backtest signals.")).toBeInTheDocument();

  resolveSignals({ signals: [] });
  await screen.findByRole("button", { name: "Previous" });
  fireEvent.click(screen.getByRole("tab", { name: "Overview" }));
  fireEvent.click(screen.getByRole("tab", { name: "Signals (1)" }));
  expect(signalsMock).toHaveBeenCalledTimes(1);
});

it("renders a stable error state when the signals request fails", async () => {
  detailMock.mockResolvedValue(detail(1));
  signalsMock.mockRejectedValue(new ApiClientError("offline", { kind: "network" }));
  render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (1)" }));

  expect(await screen.findByText("Backtest signals API unavailable: network")).toBeInTheDocument();
});

it("requests the next offset and disables Next at the exact known total", async () => {
  detailMock.mockResolvedValue(detail(40));
  signalsMock.mockImplementation((_runId, _limit, offset) => {
    const pageOffset = offset ?? 0;
    return Promise.resolve({
      signals: Array.from({ length: 20 }, (_, index) => ({
        backtest_run_id: 7,
        result: "rebalance",
        signal_date: "2026-01-02",
        signal_id: pageOffset + index + 1
      }))
    });
  });
  render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (40)" }));
  await screen.findByRole("link", { name: "Signal #20" });
  fireEvent.click(screen.getByRole("button", { name: "Next" }));

  await screen.findByRole("link", { name: "Signal #40" });
  expect(signalsMock).toHaveBeenLastCalledWith("7", 20, 20);
  expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
});

it("resets on backtestId changes and ignores the previous run's signal response", async () => {
  let resolveOldSignals!: (value: {
    signals: { backtest_run_id: number; result: string; signal_date: string; signal_id: number }[];
  }) => void;
  detailMock.mockResolvedValueOnce(detail(1, 7)).mockResolvedValueOnce(detail(1, 8));
  signalsMock
    .mockImplementationOnce(() => new Promise((resolve) => { resolveOldSignals = resolve; }))
    .mockResolvedValueOnce({
      signals: [{ backtest_run_id: 8, result: "hold", signal_date: "2026-01-03", signal_id: 8 }]
    });
  const { rerender } = render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (1)" }));
  await waitFor(() => expect(signalsMock).toHaveBeenCalledWith("7", 20, 0));

  rerender(<BacktestDetailPage backtestId="8" />);
  await screen.findByText("Backtest #8");
  expect(screen.getByRole("tab", { name: "Overview" })).toHaveAttribute("aria-selected", "true");

  resolveOldSignals({
    signals: [{ backtest_run_id: 7, result: "hold", signal_date: "2026-01-02", signal_id: 7 }]
  });
  expect(screen.queryByRole("link", { name: "Signal #7" })).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: "Signals (1)" }));
  expect(await screen.findByRole("link", { name: "Signal #8" })).toBeInTheDocument();
  expect(signalsMock).toHaveBeenLastCalledWith("8", 20, 0);
});

it("does not revive cached state during a rapid A to B to A route change", async () => {
  detailMock
    .mockResolvedValueOnce(detail(1, 7))
    .mockImplementation(() => new Promise(() => undefined));
  signalsMock.mockResolvedValue({
    signals: [{ backtest_run_id: 7, result: "hold", signal_date: "2026-01-02", signal_id: 7 }]
  });
  const { rerender } = render(<BacktestDetailPage backtestId="7" />);

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (1)" }));
  await screen.findByRole("link", { name: "Signal #7" });

  rerender(<BacktestDetailPage backtestId="8" />);
  rerender(<BacktestDetailPage backtestId="7" />);

  expect(screen.getByText("Loading backtest detail.")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Signal #7" })).not.toBeInTheDocument();
});
