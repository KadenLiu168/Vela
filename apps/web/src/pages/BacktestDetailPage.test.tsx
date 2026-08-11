import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import {
  ApiClientError,
  type BacktestDetailResponse,
  type ReturnStability,
  getBacktestDetail,
  listBacktestSignals
} from "../api/client";
import { BacktestDetailPage } from "./BacktestDetailPage";

function RouterWrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, getBacktestDetail: vi.fn(), listBacktestSignals: vi.fn() };
});

const detailMock = vi.mocked(getBacktestDetail);
const signalsMock = vi.mocked(listBacktestSignals);

const emptyStability = (): ReturnStability => ({
  strategy: {
    window_sessions: 63,
    rolling_status: "insufficient_observations",
    sharpe_status: "insufficient_observations",
    source_point_count: 0,
    effective_return_count: 0,
    rolling: [],
    monthly: [],
    yearly: []
  },
  benchmarks: []
});

const legacyTailFields = {
  historical_var_95: null,
  historical_cvar_95: null,
  return_skewness: null,
  return_excess_kurtosis: null,
  distribution_observation_count: null,
  tail_observation_count: null,
  distribution_evidence_status: "unavailable_legacy" as const
};

const detail = (signalCount: number, runId = 7): BacktestDetailResponse => ({
  benchmarks: [],
  equity_curve: [],
  metrics: {
    annualized_return: null,
    calmar_ratio: null,
    longest_drawdown_duration_sessions: null,
    longest_drawdown_peak_date: null,
    longest_drawdown_recovery_date: null,
    longest_drawdown_trough_date: null,
    max_drawdown: null,
    sharpe_ratio: null,
    sortino_ratio: null,
    total_return: null,
    volatility: null,
    ...legacyTailFields
  },
  return_stability: emptyStability(),
  run: { config_version: "v1", end_date: "2026-01-02", error_message: null, finished_at: null, parameters_json: null, run_id: runId, start_date: "2026-01-01", started_at: "2026-01-01T00:00:00", status: "success", strategy_id: "s" },
  signal_count: signalCount,
  signal_ids: []
});

afterEach(() => vi.clearAllMocks());

it("renders Overview by default with connected automatically activated tabs", async () => {
  detailMock.mockResolvedValue(detail(1));
  signalsMock.mockResolvedValue({ signals: [] });
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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
        sortino_ratio: "0.7", calmar_ratio: "1.3", longest_drawdown_duration_sessions: 2,
        longest_drawdown_peak_date: "2026-01-12", longest_drawdown_trough_date: "2026-01-18", longest_drawdown_recovery_date: null,
        tracking_error: "0.038884", information_ratio: "12.961481",
        total_return_difference: "0.02", annualized_return_difference: "0.02",
        capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
        up_capture_ratio: null, up_capture_observation_count: null,
        down_capture_ratio: null, down_capture_observation_count: null,
        equity_curve: [{ trade_date: "2026-01-01", net_value: "1" }, { trade_date: "2026-01-02", net_value: "1.1" }],
        ...legacyTailFields
      },
      {
        key: "csi_300_buy_hold",
        name: "CSI 300 buy-and-hold",
        total_return: "0.08", annualized_return: "0.08", max_drawdown: "-0.08", volatility: "0.08", sharpe_ratio: "0.8",
        sortino_ratio: null, calmar_ratio: null, longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null, longest_drawdown_trough_date: null, longest_drawdown_recovery_date: null,
        tracking_error: null, information_ratio: null,
        total_return_difference: "0.04", annualized_return_difference: "0.04",
        capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
        up_capture_ratio: null, up_capture_observation_count: null,
        down_capture_ratio: null, down_capture_observation_count: null,
        equity_curve: [{ trade_date: "2026-01-01", net_value: "1" }, { trade_date: "2026-01-02", net_value: "1.08" }],
        ...legacyTailFields
      }
    ],
    equity_curve: [
      { trade_date: "2026-01-01", net_value: "1", cash: "0", market_value: "1", total_assets: "1", positions_json: "[]" },
      { trade_date: "2026-01-02", net_value: "1.12", cash: "0", market_value: "1.12", total_assets: "1.12", positions_json: "[]" }
    ]
  });
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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

it("renders expanded strategy and relative benchmark metrics with ongoing and unavailable values", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    metrics: {
      ...detail(0).metrics,
      sortino_ratio: "1.234567",
      calmar_ratio: "2.345678",
      longest_drawdown_duration_sessions: 3,
      longest_drawdown_peak_date: "2026-01-10",
      longest_drawdown_trough_date: "2026-01-20",
      longest_drawdown_recovery_date: null
    },
    benchmarks: [
      {
        key: "equal_weight_monthly",
        name: "Equal-weight monthly rebalanced portfolio",
        total_return: null,
        annualized_return: null,
        max_drawdown: null,
        volatility: null,
        sharpe_ratio: null,
        sortino_ratio: null,
        calmar_ratio: null,
        longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null,
        longest_drawdown_trough_date: null,
        longest_drawdown_recovery_date: null,
        tracking_error: "0.038884",
        information_ratio: "12.961481",
        total_return_difference: null,
        annualized_return_difference: null,
        capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
        up_capture_ratio: null, up_capture_observation_count: null,
        down_capture_ratio: null, down_capture_observation_count: null,
        equity_curve: [],
        ...legacyTailFields
      }
    ]
  });

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByText("Backtest #7");
  expect(screen.getAllByText("Sortino (rf MAR, 252D)").length).toBe(2);
  expect(screen.getByText("1.234567")).toBeInTheDocument();
  expect(screen.getAllByText("Calmar (calendar CAGR / |MaxDD|)").length).toBe(2);
  expect(screen.getByText("2.345678")).toBeInTheDocument();
  expect(screen.getAllByText("Longest drawdown duration (official sessions)").length).toBe(2);
  expect(screen.getByText("3")).toBeInTheDocument();
  expect(screen.getByText("2026-01-10")).toBeInTheDocument();
  expect(screen.getByText("2026-01-20")).toBeInTheDocument();
  expect(screen.getByText("ongoing")).toBeInTheDocument();
  expect(screen.getByText("Tracking error (252D)")).toBeInTheDocument();
  expect(screen.getByText("0.038884")).toBeInTheDocument();
  expect(screen.getByText("Information ratio (252D)")).toBeInTheDocument();
  expect(screen.getByText("12.961481")).toBeInTheDocument();
  expect(screen.getAllByText("n/a").length).toBeGreaterThan(0);
});

it("renders proxy-qualified CAPM and monthly capture evidence with count units", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    benchmarks: [
      {
        key: "equal_weight_monthly",
        name: "Equal-weight monthly rebalanced portfolio",
        total_return: "0.1", annualized_return: "0.1", max_drawdown: "-0.1", volatility: "0.1", sharpe_ratio: "1",
        sortino_ratio: null, calmar_ratio: null, longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null, longest_drawdown_trough_date: null, longest_drawdown_recovery_date: null,
        tracking_error: null, information_ratio: null,
        total_return_difference: null, annualized_return_difference: null,
        capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
        up_capture_ratio: "1.995274", up_capture_observation_count: 2,
        down_capture_ratio: "0.5", down_capture_observation_count: 1,
        equity_curve: [],
        ...legacyTailFields
      },
      {
        key: "csi_300_buy_hold",
        name: "CSI 300 buy-and-hold",
        total_return: "0.08", annualized_return: "0.08", max_drawdown: "-0.08", volatility: "0.08", sharpe_ratio: "0.8",
        sortino_ratio: null, calmar_ratio: null, longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null, longest_drawdown_trough_date: null, longest_drawdown_recovery_date: null,
        tracking_error: null, information_ratio: null,
        total_return_difference: null, annualized_return_difference: null,
        capm_alpha: "11.274002", capm_beta: "2.000000", capm_r_squared: "0.958580", capm_observation_count: 4,
        up_capture_ratio: "1.995274", up_capture_observation_count: 2,
        down_capture_ratio: "0.5", down_capture_observation_count: 1,
        equity_curve: [],
        ...legacyTailFields
      }
    ]
  });
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByRole("heading", { name: "CSI 300 buy-and-hold" });
  expect(screen.getByText("CSI 300 ETF proxy Alpha (252D compounded)")).toBeInTheDocument();
  expect(screen.getByText("1127.40%")).toBeInTheDocument();
  expect(screen.getByText("Beta (CSI 300 ETF proxy)")).toBeInTheDocument();
  expect(screen.getByText("2.000000")).toBeInTheDocument();
  expect(screen.getByText("R-squared (CSI 300 ETF proxy)")).toBeInTheDocument();
  expect(screen.getByText("0.958580")).toBeInTheDocument();
  expect(screen.getByText("CAPM observations (daily sessions)")).toBeInTheDocument();
  expect(screen.getByText("4")).toBeInTheDocument();
  expect(screen.getAllByText("Monthly Up Capture (selected months)").length).toBe(2);
  expect(screen.getAllByText("199.53%").length).toBe(2);
  expect(screen.getAllByText("Up selected months").length).toBe(2);
  expect(screen.getAllByText("Monthly Down Capture (selected months)").length).toBe(2);
  expect(screen.getAllByText("50.00%").length).toBe(2);
  expect(screen.getAllByText("Down selected months").length).toBe(2);
  // CAPM lines appear only once (the CSI 300 group); the equal-weight group
  // never presents equal-weight results as CAPM.
  expect(screen.getAllByText("Beta (CSI 300 ETF proxy)").length).toBe(1);
  expect(screen.getAllByText("CSI 300 ETF proxy Alpha (252D compounded)").length).toBe(1);
});

it("renders unavailable placeholders for legacy or undefined regime values", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    benchmarks: [
      {
        key: "csi_300_buy_hold",
        name: "CSI 300 buy-and-hold",
        total_return: null, annualized_return: null, max_drawdown: null, volatility: null, sharpe_ratio: null,
        sortino_ratio: null, calmar_ratio: null, longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null, longest_drawdown_trough_date: null, longest_drawdown_recovery_date: null,
        tracking_error: null, information_ratio: null,
        total_return_difference: null, annualized_return_difference: null,
        capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
        up_capture_ratio: null, up_capture_observation_count: null,
        down_capture_ratio: null, down_capture_observation_count: null,
        equity_curve: [],
        ...legacyTailFields
      }
    ]
  });
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByRole("heading", { name: "CSI 300 buy-and-hold" });
  expect(screen.getAllByText("n/a").length).toBeGreaterThan(0);
  expect(screen.queryByText("NaN")).not.toBeInTheDocument();
  expect(screen.queryByText("Infinity")).not.toBeInTheDocument();
});

it.each([
  [1440, 1000],
  [390, 844]
])("renders benchmark regime groups, labels, counts, and tabs without overflow at %ipx wide", async (width, height) => {
  Object.defineProperty(window, "innerWidth", { value: width, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: height, configurable: true, writable: true });
  detailMock.mockResolvedValue({
    ...detail(1),
    benchmarks: [
      {
        key: "equal_weight_monthly",
        name: "Equal-weight monthly rebalanced portfolio",
        total_return: "0.1", annualized_return: "0.1", max_drawdown: "-0.1", volatility: "0.1", sharpe_ratio: "1",
        sortino_ratio: null, calmar_ratio: null, longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null, longest_drawdown_trough_date: null, longest_drawdown_recovery_date: null,
        tracking_error: null, information_ratio: null,
        total_return_difference: null, annualized_return_difference: null,
        capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
        up_capture_ratio: "1.2", up_capture_observation_count: 8,
        down_capture_ratio: "0.7", down_capture_observation_count: 3,
        equity_curve: [],
        ...legacyTailFields
      },
      {
        key: "csi_300_buy_hold",
        name: "CSI 300 buy-and-hold",
        total_return: "0.08", annualized_return: "0.08", max_drawdown: "-0.08", volatility: "0.08", sharpe_ratio: "0.8",
        sortino_ratio: null, calmar_ratio: null, longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null, longest_drawdown_trough_date: null, longest_drawdown_recovery_date: null,
        tracking_error: null, information_ratio: null,
        total_return_difference: null, annualized_return_difference: null,
        capm_alpha: "0.5", capm_beta: "1.1", capm_r_squared: "0.8", capm_observation_count: 240,
        up_capture_ratio: "1.2", up_capture_observation_count: 8,
        down_capture_ratio: "0.7", down_capture_observation_count: 3,
        equity_curve: [],
        ...legacyTailFields
      }
    ]
  });

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByRole("heading", { name: "CSI 300 buy-and-hold" });
  expect(screen.getByRole("heading", { name: "Equal-weight monthly rebalanced portfolio" })).toBeInTheDocument();
  expect(screen.getByText("CSI 300 ETF proxy Alpha (252D compounded)")).toBeInTheDocument();
  expect(screen.getAllByText("Monthly Up Capture (selected months)").length).toBe(2);
  expect(screen.getAllByText("Up selected months").length).toBe(2);
  expect(screen.getAllByText("Down selected months").length).toBe(2);
  expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Signals (1)" })).toBeInTheDocument();
  expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(width);
});

it("wraps ArrowLeft and ArrowRight and supports Home and End", async () => {
  detailMock.mockResolvedValue(detail(0));
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (0)" }));
  expect(signalsMock).not.toHaveBeenCalled();
  expect(screen.getByText("No signals are linked to this backtest.")).toBeInTheDocument();
});

it("renders the signals table and uses signal_count for an exact final-page boundary", async () => {
  detailMock.mockResolvedValue(detail(20));
  signalsMock.mockResolvedValue({ signals: Array.from({ length: 20 }, (_, index) => ({ backtest_run_id: 7, result: "rebalance", signal_date: "2026-01-02", signal_id: 80 + index })) });
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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
  const { rerender } = render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

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
  const { rerender } = render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByText("Backtest #7");
  fireEvent.click(screen.getByRole("tab", { name: "Signals (1)" }));
  await screen.findByRole("link", { name: "Signal #7" });

  rerender(<BacktestDetailPage backtestId="8" />);
  rerender(<BacktestDetailPage backtestId="7" />);

  expect(screen.getByText("Loading backtest detail.")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Signal #7" })).not.toBeInTheDocument();
});

const stabilityDetail = (overrides: Partial<ReturnStability> = {}): BacktestDetailResponse => ({
  ...detail(0),
  return_stability: {
    strategy: {
      window_sessions: 63,
      rolling_status: "available",
      sharpe_status: "available",
      source_point_count: 66,
      effective_return_count: 65,
      rolling: [
        { window_start_date: "2026-01-01", trade_date: "2026-03-31", total_return: "0.123456", volatility: "0.182345", sharpe_ratio: "0.871234" },
        { window_start_date: "2026-01-02", trade_date: "2026-04-01", total_return: "0.130000", volatility: "0.190000", sharpe_ratio: "0.900000" }
      ],
      monthly: [
        { period: "2026-01", first_date: "2026-01-02", last_date: "2026-01-30", observation_count: 21, total_return: "0.030000", is_partial: false },
        { period: "2026-02", first_date: "2026-02-02", last_date: "2026-02-27", observation_count: 20, total_return: "-0.010000", is_partial: true }
      ],
      yearly: [
        { period: "2026", first_date: "2026-01-02", last_date: "2026-04-01", observation_count: 65, total_return: "0.130000", is_partial: true }
      ]
    },
    benchmarks: [],
    ...overrides
  }
});

it.each([
  [1440, 1000],
  [390, 844]
])("renders stability selectors, charts, exact values, and partial markers without page overflow at %ipx wide", async (width, height) => {
  Object.defineProperty(window, "innerWidth", { value: width, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: height, configurable: true, writable: true });
  detailMock.mockResolvedValue(stabilityDetail());

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByText("Backtest #7");
  expect(screen.getByRole("heading", { name: "Return stability" })).toBeInTheDocument();
  expect(screen.getByRole("group", { name: "Rolling metric selector" })).toBeInTheDocument();
  expect(screen.getByRole("list", { name: "Rolling Return legend" })).toBeInTheDocument();
  expect(screen.getAllByText("0.123456").length).toBeGreaterThan(0);
  expect(screen.getAllByText("partial").length).toBeGreaterThan(0);
  expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Signals (0)" })).toBeInTheDocument();
  expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(width);
});

it("keeps existing Overview tabs and actions when stability is present", async () => {
  detailMock.mockResolvedValue(stabilityDetail({ strategy: { ...stabilityDetail().return_stability.strategy, rolling_status: "insufficient_observations", rolling: [] } }));

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByText("Backtest #7");
  expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Signals (0)" })).toBeInTheDocument();
  expect(screen.getByText(/Fewer than 64 persisted points/)).toBeInTheDocument();
});

const tailFields = (
  overrides: {
    historical_var_95?: string | null;
    historical_cvar_95?: string | null;
    return_skewness?: string | null;
    return_excess_kurtosis?: string | null;
    distribution_observation_count?: number | null;
    tail_observation_count?: number | null;
    distribution_evidence_status?: "sufficient" | "insufficient_evidence" | "unavailable_legacy";
  } = {}
) => ({
  historical_var_95: "0.020000",
  historical_cvar_95: "0.060000",
  return_skewness: "0.123456",
  return_excess_kurtosis: "0.654321",
  distribution_observation_count: 100,
  tail_observation_count: 5,
  distribution_evidence_status: "sufficient" as const,
  ...overrides
});

it("renders sufficient one-day historical distribution risk with exact API values", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    metrics: { ...detail(0).metrics, ...tailFields() }
  });

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByRole("heading", { name: "One-day historical distribution risk (95%)" });
  expect(screen.getByText("Historical VaR 95% (1D loss)")).toBeInTheDocument();
  expect(screen.getByText("Historical CVaR 95% (1D loss)")).toBeInTheDocument();
  expect(screen.getByText("Skewness")).toBeInTheDocument();
  expect(screen.getByText("Excess kurtosis (normal = 0)")).toBeInTheDocument();
  expect(screen.getByText("0.020000")).toBeInTheDocument();
  expect(screen.getByText("0.060000")).toBeInTheDocument();
  expect(screen.getByText("0.123456")).toBeInTheDocument();
  expect(screen.getByText("0.654321")).toBeInTheDocument();
  expect(screen.getAllByText("100")).toHaveLength(1);
  expect(screen.getAllByText("5")).toHaveLength(1);
  expect(
    screen.getByText(/No forecast or regulatory-capital claim/i)
  ).toBeInTheDocument();
});

it("explains the 99-observation tail-count cardinality and null metrics", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    metrics: {
      ...detail(0).metrics,
      ...tailFields({
        historical_var_95: null,
        historical_cvar_95: null,
        return_skewness: null,
        return_excess_kurtosis: null,
        distribution_observation_count: 99,
        distribution_evidence_status: "insufficient_evidence"
      })
    }
  });

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  const heading = await screen.findByRole("heading", {
    name: "One-day historical distribution risk (95%)"
  });
  const section = heading.closest("section");
  expect(section).not.toBeNull();
  expect(within(section as HTMLElement).getAllByText("n/a")).toHaveLength(4);
  expect(within(section as HTMLElement).getByText("99")).toBeInTheDocument();
  expect(within(section as HTMLElement).getByText("5")).toBeInTheDocument();
  expect(
    within(section as HTMLElement).getByText(/publication requires at least 100 effective observations/i)
  ).toBeInTheDocument();
  expect(
    within(section as HTMLElement).getByText(/tail count of 5 is the cardinality implied by the fixed 5% rank rule/i)
  ).toBeInTheDocument();
});

it("distinguishes legacy and constant-distribution null explanations", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    metrics: {
      ...detail(0).metrics,
      ...tailFields({
        return_skewness: null,
        return_excess_kurtosis: null
      })
    },
    benchmarks: []
  });

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByRole("heading", { name: "One-day historical distribution risk (95%)" });
  expect(screen.getByText(/Constant distribution: return shape statistics are undefined/i)).toBeInTheDocument();
  expect(screen.getByText("0.020000")).toBeInTheDocument();

  detailMock.mockResolvedValue({ ...detail(0), metrics: { ...detail(0).metrics } });
  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });
  expect(await screen.findByText(/Legacy history: one-day historical distribution metrics were not recorded/i)).toBeInTheDocument();
});

it("renders strategy and benchmark distribution groups with owner-specific values", async () => {
  detailMock.mockResolvedValue({
    ...detail(0),
    metrics: { ...detail(0).metrics, ...tailFields() },
    benchmarks: [
      {
        key: "equal_weight_monthly",
        name: "Equal-weight monthly rebalanced portfolio",
        total_return: "0.1", annualized_return: "0.1", max_drawdown: "-0.1", volatility: "0.1", sharpe_ratio: "1",
        sortino_ratio: null, calmar_ratio: null, longest_drawdown_duration_sessions: null,
        longest_drawdown_peak_date: null, longest_drawdown_trough_date: null, longest_drawdown_recovery_date: null,
        tracking_error: null, information_ratio: null,
        total_return_difference: "0.02", annualized_return_difference: "0.02",
        capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
        up_capture_ratio: null, up_capture_observation_count: null,
        down_capture_ratio: null, down_capture_observation_count: null,
        equity_curve: [],
        ...tailFields({
          historical_var_95: "0.010000",
          historical_cvar_95: "0.030000",
          return_skewness: "-0.500000",
          return_excess_kurtosis: "2.000000"
        })
      }
    ]
  });

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByText("Equal-weight monthly rebalanced portfolio");
  expect(screen.getAllByText("0.010000")).toHaveLength(1);
  expect(screen.getAllByText("0.030000")).toHaveLength(1);
  expect(screen.getAllByText("-0.500000")).toHaveLength(1);
  expect(screen.getAllByText("2.000000")).toHaveLength(1);
});

it.each([
  [1440, 1000],
  [390, 844]
])("keeps tail distribution risk content and actions readable without overflow at %ipx wide", async (width, height) => {
  Object.defineProperty(window, "innerWidth", { value: width, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: height, configurable: true, writable: true });
  detailMock.mockResolvedValue({
    ...detail(0),
    metrics: { ...detail(0).metrics, ...tailFields() }
  });

  render(<BacktestDetailPage backtestId="7" />, { wrapper: RouterWrapper });

  await screen.findByRole("heading", { name: "One-day historical distribution risk (95%)" });
  expect(screen.getByText("Historical VaR 95% (1D loss)")).toBeInTheDocument();
  expect(screen.getByText("Excess kurtosis (normal = 0)")).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Overview" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Signals (0)" })).toBeInTheDocument();
  expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(width);
});
