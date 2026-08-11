import { render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ApiClientError, getWalkForwardDetail, type WalkForwardDetailResponse } from "../api/client";
import { WalkForwardDetailPage } from "./WalkForwardDetailPage";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, getWalkForwardDetail: vi.fn() };
});

const detailMock = vi.mocked(getWalkForwardDetail);

afterEach(() => vi.clearAllMocks());

function metric(value: number | null = 0.12) {
  return {
    mean: value,
    median: value,
    min: value,
    max: value,
    std: 0.01,
    window_count: 2,
    valid_count: value === null ? 0 : 2,
    evidence_status: "insufficient_evidence" as const
  };
}

const detail: WalkForwardDetailResponse = {
  run: {
    run_id: 42,
    strategy_id: "dual_momentum",
    start_date: "2026-01-01",
    end_date: "2026-12-31",
    window_count: 2,
    provenance_version: "wf_provenance_v1",
    evidence_version: "wf_evidence_v1",
    config_checksum: "a".repeat(64),
    input_data_checksum: "b".repeat(64),
    status: "success",
    error_message: null,
    attempt_count: 1,
    claimed_at: "2026-12-01T00:00:00",
    heartbeat_at: "2026-12-01T00:00:15",
    lease_expires_at: "2026-12-01T00:02:00",
    started_at: "2026-12-01T00:00:00",
    finished_at: "2026-12-02T00:00:00",
    created_at: "2026-12-02T00:00:00"
  },
  configuration: {
    walk_forward: { train_window_days: 120, test_window_days: 20 },
    base_strategy: { strategy_id: "dual_momentum", version: "v1" },
    config_checksum: "a".repeat(64)
  },
  input_provenance: {
    manifest: {
      version: "wf_provenance_v1",
      earliest_required_session: "2025-09-01",
      configured_end_date: "2026-12-31",
      first_loaded_price_date: "2025-09-01",
      last_loaded_price_date: "2026-12-31",
      following_session: "2027-01-04",
      official_sessions: ["2025-09-01", "2026-12-31"],
      loaded_price_row_count: 2,
      active_etfs: [
        {
          etf_id: 7,
          exchange: "SSE",
          symbol: "510300",
          inception_date: "2012-05-28",
          loaded_price_row_count: 2,
          first_loaded_price_date: "2025-09-01",
          last_loaded_price_date: "2026-12-31"
        }
      ]
    },
    input_data_checksum: "b".repeat(64)
  },
  evidence_version: "wf_evidence_v1",
  evidence: {
    metrics: {
      total_return: metric(),
      annualized_return: metric(0.08),
      max_drawdown: metric(-0.2),
      volatility: metric(0.15),
      sharpe_ratio: metric(1.1),
      sortino_ratio: metric(1.4),
      calmar_ratio: metric(0.5),
      longest_drawdown_duration_sessions: metric(8)
    },
    positive_window_rate: {
      numerator: 2,
      denominator: 2,
      value: 1,
      window_count: 2,
      valid_count: 2,
      evidence_status: "insufficient_evidence"
    },
    generalization_gap: metric(0.03),
    benchmarks: {
      equal_weight_monthly: {
        total_return_difference: metric(0.01),
        annualized_return_difference: metric(0.02),
        tracking_error: metric(0.04),
        information_ratio: metric(0.6),
        outperformance_rate: {
          numerator: 1,
          denominator: 2,
          value: 0.5,
          window_count: 2,
          valid_count: 2,
          evidence_status: "insufficient_evidence"
        }
      },
      csi_300_buy_hold: {
        total_return_difference: metric(0.02),
        annualized_return_difference: metric(0.03),
        tracking_error: metric(0.05),
        information_ratio: metric(0.7),
        outperformance_rate: {
          numerator: 1,
          denominator: 2,
          value: 0.5,
          window_count: 2,
          valid_count: 2,
          evidence_status: "insufficient_evidence"
        }
      }
    },
    parameter_stability: {
      lookback_days: {
        value_frequencies: { "120": 2 },
        transition_count: 0,
        comparison_count: 1,
        transition_rate: 0
      }
    }
  },
  stitched_oos: {
    status: "available",
    initial_net_value: "1.000000",
    ending_net_value: "0.990000",
    total_return: "-0.010000",
    points: [
      { trade_date: "2025-06-01", net_value: "1.000000", window_ordinal: 0, is_window_start: true },
      { trade_date: "2025-06-30", net_value: "1.100000", window_ordinal: 0, is_window_start: false },
      { trade_date: "2025-07-01", net_value: "1.100000", window_ordinal: 1, is_window_start: true },
      { trade_date: "2025-07-31", net_value: "0.990000", window_ordinal: 1, is_window_start: false }
    ]
  },
  windows: [
    {
      ordinal: 0,
      train_start: "2025-01-01",
      train_end: "2025-05-31",
      test_start: "2025-06-01",
      test_end: "2025-06-30",
      oos_version: "v1",
      selected_parameters: { lookback_days: 120 },
      candidate_count: 3,
      eligible_count: 2,
      skipped_count: 1,
      skip_reason_counts: { invalid_config: 1 },
      train_sharpe: "1.10",
      oos_backtest: {
        run_id: 100,
        strategy_id: "dual_momentum",
        config_version: "wf-000000000001",
        start_date: "2025-06-01",
        end_date: "2025-06-30",
        status: "success",
        total_return: "0.10",
        annualized_return: "0.20",
        max_drawdown: "-0.05",
        volatility: "0.12",
        sharpe_ratio: "1.2",
        sortino_ratio: "1.3",
        calmar_ratio: "2.0",
        longest_drawdown_duration_sessions: 3,
        longest_drawdown_peak_date: "2025-06-10",
        longest_drawdown_trough_date: "2025-06-12",
            longest_drawdown_recovery_date: null,
        benchmarks: [
          {
            key: "equal_weight_monthly",
            name: "Equal weight monthly",
            total_return: "0.08",
            annualized_return: "0.16",
            max_drawdown: "-0.04",
            volatility: "0.11",
            sharpe_ratio: "1.0",
            sortino_ratio: "1.1",
            calmar_ratio: "1.8",
            longest_drawdown_duration_sessions: 2,
            longest_drawdown_peak_date: "2025-06-10",
            longest_drawdown_trough_date: "2025-06-11",
            longest_drawdown_recovery_date: "2025-06-14",
            total_return_difference: "0.02",
            annualized_return_difference: "0.04",
            tracking_error: "0.03",
            information_ratio: "0.7",
            capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
            up_capture_ratio: null, up_capture_observation_count: null,
            down_capture_ratio: null, down_capture_observation_count: null
          },
          {
            key: "csi_300_buy_hold",
            name: "CSI 300 buy and hold",
            total_return: "0.07",
            annualized_return: "0.15",
            max_drawdown: "-0.03",
            volatility: "0.10",
            sharpe_ratio: "0.9",
            sortino_ratio: "1.0",
            calmar_ratio: "1.7",
            longest_drawdown_duration_sessions: 4,
            longest_drawdown_peak_date: "2025-06-09",
            longest_drawdown_trough_date: "2025-06-12",
            longest_drawdown_recovery_date: null,
            total_return_difference: "0.03",
            annualized_return_difference: "0.05",
            tracking_error: "0.04",
            information_ratio: "0.8",
            capm_alpha: null, capm_beta: null, capm_r_squared: null, capm_observation_count: null,
            up_capture_ratio: null, up_capture_observation_count: null,
            down_capture_ratio: null, down_capture_observation_count: null
          }
        ]
      }
    }
  ]
};

const detailEvidence = detail.evidence as NonNullable<WalkForwardDetailResponse["evidence"]>;

it("presents persisted evidence, provenance, candidates, and stitched OOS reset semantics", async () => {
  detailMock.mockResolvedValue(detail);

  render(<WalkForwardDetailPage runId="42" />);

  expect(await screen.findByText("Walk-forward #42")).toBeInTheDocument();
  expect(screen.getByText("Total return")).toBeInTheDocument();
  expect(screen.getByText("Annualized return")).toBeInTheDocument();
  expect(screen.getByText("Max drawdown")).toBeInTheDocument();
  expect(screen.getByText("Volatility")).toBeInTheDocument();
  expect(screen.getByText("Sharpe ratio")).toBeInTheDocument();
  expect(screen.getByText("Sortino ratio")).toBeInTheDocument();
  expect(screen.getByText("Calmar ratio")).toBeInTheDocument();
  expect(screen.getByText("Longest drawdown duration")).toBeInTheDocument();
  expect(screen.getByText(/minimum-valid-count threshold/)).toBeInTheDocument();
  expect(screen.getByText(/configuration paths are display metadata/i)).toBeInTheDocument();
  expect(screen.getByText("wf_provenance_v1")).toBeInTheDocument();
  expect(screen.getByText("2027-01-04")).toBeInTheDocument();
  expect(screen.getByText(/Candidates: 3/)).toBeInTheDocument();
  expect(screen.getByText(/invalid_config: 1/)).toBeInTheDocument();
  expect(screen.getByText("Transitions").nextElementSibling).toHaveTextContent("0/1");
  const totalReturn = screen.getByLabelText("Total return summary");
  expect(within(totalReturn).getByText("Median: 0.12")).toBeInTheDocument();
  expect(within(totalReturn).getByText("Population std: 0.01")).toBeInTheDocument();
  expect(screen.getByText("100.00% (2/2); 2/2 valid; insufficient_evidence")).toBeInTheDocument();
  expect(screen.getByText("Generalization gap").nextElementSibling).toHaveTextContent(
    "mean 0.03; median 0.03; range 0.03 to 0.03"
  );
  const oosMetrics = screen.getByLabelText("OOS strategy metrics for window 0");
  expect(within(oosMetrics).getByText("Sortino: 1.3")).toBeInTheDocument();
  expect(within(oosMetrics).getByText("Calmar: 2")).toBeInTheDocument();
  const equalWeight = screen.getByLabelText("Equal weight monthly metrics for window 0");
  expect(within(equalWeight).getByText("Tracking error: 0.03")).toBeInTheDocument();
  expect(within(equalWeight).getByText("Recovery: 2025-06-14")).toBeInTheDocument();
  const csi300 = screen.getByLabelText("CSI 300 buy and hold metrics for window 0");
  expect(within(csi300).getByText("Information ratio: 0.8")).toBeInTheDocument();
  expect(within(csi300).getByText("Recovery: ongoing")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Backtest #100" })).toHaveAttribute("href", "/backtests/100");
  const stitchedChart = screen.getByRole("img", { name: /stitched OOS equity curve/i });
  expect(stitchedChart).toBeInTheDocument();
  expect(stitchedChart.querySelector("path")).toHaveAttribute("stroke", "var(--color-acid-lime)");
  expect(screen.getByText("0.990000")).toBeInTheDocument();
  expect(screen.getByText("-0.010000")).toBeInTheDocument();
  expect(screen.getByText(/Window 2 reset: 2025-07-01/)).toBeInTheDocument();
  expect(screen.getByText(/No seam return, holdings carry, turnover, or transaction cost/)).toBeInTheDocument();
  expect(screen.queryByText(/score|pass|fail/i)).not.toBeInTheDocument();
});

const v2Detail: WalkForwardDetailResponse = {
  ...detail,
  run: { ...detail.run, evidence_version: "wf_evidence_v2" },
  evidence_version: "wf_evidence_v2",
  evidence: {
    ...detailEvidence,
    benchmarks: {
      equal_weight_monthly: {
        ...detailEvidence.benchmarks.equal_weight_monthly,
        up_capture_ratio: metric(1.2),
        down_capture_ratio: metric(0.7)
      },
      csi_300_buy_hold: {
        ...detailEvidence.benchmarks.csi_300_buy_hold,
        capm_alpha: metric(0.5),
        capm_beta: metric(1.1),
        capm_r_squared: metric(0.8),
        up_capture_ratio: metric(1.2),
        down_capture_ratio: metric(0.7)
      }
    }
  },
  windows: [
    {
      ...detail.windows[0],
      oos_backtest: {
        ...detail.windows[0].oos_backtest,
        benchmarks: [
          {
            ...detail.windows[0].oos_backtest.benchmarks[0],
            up_capture_ratio: "1.2",
            up_capture_observation_count: 8,
            down_capture_ratio: "0.7",
            down_capture_observation_count: 3
          },
          {
            ...detail.windows[0].oos_backtest.benchmarks[1],
            capm_alpha: "0.5",
            capm_beta: "1.1",
            capm_r_squared: "0.8",
            capm_observation_count: 240,
            up_capture_ratio: "1.2",
            up_capture_observation_count: 8,
            down_capture_ratio: "0.7",
            down_capture_observation_count: 3
          }
        ]
      }
    }
  ]
};

it("presents v2 benchmark-regime aggregates and per-window evidence with count units", async () => {
  detailMock.mockResolvedValue(v2Detail);

  render(<WalkForwardDetailPage runId="42" />);

  await screen.findByText("Walk-forward #42");
  expect(screen.getByText("wf_evidence_v2")).toBeInTheDocument();
  expect(screen.getByText("CSI 300 ETF proxy Alpha (252D compounded)")).toBeInTheDocument();
  expect(screen.getByText("Beta (CSI 300 ETF proxy)")).toBeInTheDocument();
  expect(screen.getByText("R-squared (CSI 300 ETF proxy)")).toBeInTheDocument();
  expect(screen.getAllByText("Monthly Up Capture (selected months)").length).toBe(2);
  expect(screen.getAllByText("Monthly Down Capture (selected months)").length).toBe(2);
  const csiWindow = screen.getByLabelText("CSI 300 buy and hold metrics for window 0");
  expect(within(csiWindow).getByText("CSI 300 ETF proxy Alpha (252D compounded): 0.5")).toBeInTheDocument();
  expect(within(csiWindow).getByText("CAPM observations (daily sessions): 240")).toBeInTheDocument();
  expect(within(csiWindow).getByText("Up selected months: 8")).toBeInTheDocument();
  expect(within(csiWindow).getByText("Down selected months: 3")).toBeInTheDocument();
  const equalWeightWindow = screen.getByLabelText("Equal weight monthly metrics for window 0");
  expect(within(equalWeightWindow).queryByText(/Alpha/)).not.toBeInTheDocument();
  expect(within(equalWeightWindow).getByText("Monthly Up Capture (selected months): 1.2")).toBeInTheDocument();
  // Existing evidence and navigation remain available.
  expect(screen.getByRole("link", { name: "Backtest #100" })).toHaveAttribute("href", "/backtests/100");
  expect(screen.queryByText(/score|pass|fail/i)).not.toBeInTheDocument();
});

it.each([
  [1440, 1000],
  [390, 844]
])("renders v2 regime groups, labels, counts, and navigation without overflow at %ipx wide", async (width, height) => {
  Object.defineProperty(window, "innerWidth", { value: width, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: height, configurable: true, writable: true });
  detailMock.mockResolvedValue(v2Detail);

  render(<WalkForwardDetailPage runId="42" />);

  expect(await screen.findByText("wf_evidence_v2")).toBeInTheDocument();
  expect(screen.getByText("CSI 300 ETF proxy Alpha (252D compounded)")).toBeInTheDocument();
  expect(screen.getAllByText("Monthly Up Capture (selected months)").length).toBe(2);
  expect(screen.getAllByText("Monthly Down Capture (selected months)").length).toBe(2);
  expect(screen.getAllByText(/Up selected months: 8/).length).toBe(2);
  expect(screen.getAllByText(/Down selected months: 3/).length).toBe(2);
  expect(screen.getByRole("link", { name: "Backtest #100" })).toHaveAttribute("href", "/backtests/100");
  expect(screen.getByRole("img", { name: /stitched OOS equity curve/i })).toBeInTheDocument();
  expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(width);
});

it("keeps legacy v1 evidence without fabricated regime values", async () => {
  detailMock.mockResolvedValue(detail);

  render(<WalkForwardDetailPage runId="42" />);

  await screen.findByText("Walk-forward #42");
  expect(screen.getByText("wf_evidence_v1")).toBeInTheDocument();
  expect(screen.queryByText("CSI 300 ETF proxy Alpha (252D compounded)")).not.toBeInTheDocument();
  expect(screen.queryByText("Monthly Up Capture (selected months)")).not.toBeInTheDocument();
});

it("renders explicit not-found and unexpected-error states", async () => {
  detailMock.mockRejectedValueOnce(new ApiClientError("not found", { kind: "http", status: 404, category: "not_found" }));
  const { unmount } = render(<WalkForwardDetailPage runId="404" />);
  expect(await screen.findByText("Walk-forward run 404 was not found.")).toBeInTheDocument();
  unmount();

  detailMock.mockRejectedValueOnce(new ApiClientError("network", { kind: "network" }));
  render(<WalkForwardDetailPage runId="500" />);
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("network"));
});

it("ignores a stale detail response when the route id changes", async () => {
  let resolveOld!: (value: WalkForwardDetailResponse) => void;
  detailMock.mockImplementation((runId) => {
    if (runId === "1") {
      return new Promise((resolve) => {
        resolveOld = resolve;
      });
    }
    return Promise.resolve({
      ...detail,
      run: { ...detail.run, run_id: Number(runId) }
    });
  });

  const { rerender } = render(<WalkForwardDetailPage runId="1" />);
  rerender(<WalkForwardDetailPage runId="2" />);
  expect(await screen.findByText("Walk-forward #2")).toBeInTheDocument();

  resolveOld(detail);
  await waitFor(() => expect(screen.queryByText("Walk-forward #1")).not.toBeInTheDocument());
  expect(screen.getByText("Walk-forward #2")).toBeInTheDocument();
});

it("preserves complete evidence when stitched OOS is unavailable for non-contiguous windows", async () => {
  detailMock.mockResolvedValue({
    ...detail,
    stitched_oos: {
      status: "unavailable_non_contiguous_windows",
      initial_net_value: null,
      ending_net_value: null,
      total_return: null,
      points: []
    }
  });

  render(<WalkForwardDetailPage runId="42" />);

  expect(await screen.findByText("Walk-forward #42")).toBeInTheDocument();
  const section = screen.getByRole("heading", { name: "Stitched OOS capital path" }).closest("section");
  expect(section).not.toBeNull();
  expect(within(section as HTMLElement).getByText(/Gap or overlap windows cannot form one chronological capital path/)).toBeInTheDocument();
  expect(within(section as HTMLElement).queryByRole("img", { name: /stitched OOS equity curve/i })).not.toBeInTheDocument();
  expect(within(section as HTMLElement).queryByText("0.990000")).not.toBeInTheDocument();
  expect(within(section as HTMLElement).queryByText("-0.010000")).not.toBeInTheDocument();
  expect(screen.getByText("Total return")).toBeInTheDocument();
  expect(screen.getByText("Sharpe ratio")).toBeInTheDocument();
  expect(screen.getByText(/Candidates: 3/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Backtest #100" })).toHaveAttribute("href", "/backtests/100");
  expect(screen.queryByText(/Window 2 reset/)).not.toBeInTheDocument();
});

it("does not fabricate stitched OOS evidence for an active run", async () => {
  detailMock.mockResolvedValue({
    ...detail,
    run: {
      ...detail.run,
      status: "queued",
      window_count: 0,
      finished_at: null,
      error_message: null
    },
    evidence: null,
    windows: [],
    stitched_oos: null
  });

  render(<WalkForwardDetailPage runId="42" />);

  expect(await screen.findByText(/Evidence is unavailable until this queued run/)).toBeInTheDocument();
  expect(
    screen.queryByRole("heading", { name: "Stitched OOS capital path" })
  ).not.toBeInTheDocument();
  expect(screen.getByText(/No OOS windows have been published/)).toBeInTheDocument();
  expect(screen.queryByText(/stitched capital path above/)).not.toBeInTheDocument();
  expect(screen.queryByRole("link", { name: /Backtest #/ })).not.toBeInTheDocument();
});

it.each([
  [1440, 1000],
  [390, 844]
])("renders the stitched OOS section without page-level overflow at %ipx wide", async (width, height) => {
  Object.defineProperty(window, "innerWidth", { value: width, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: height, configurable: true, writable: true });
  detailMock.mockResolvedValue(detail);

  render(<WalkForwardDetailPage runId="42" />);

  expect(await screen.findByRole("heading", { name: "Stitched OOS capital path" })).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /stitched OOS equity curve/i })).toBeInTheDocument();
  expect(screen.getByRole("list", { name: "Stitched OOS window resets" })).toBeInTheDocument();
  expect(screen.getByText("0.990000")).toBeInTheDocument();
  expect(screen.getByText("-0.010000")).toBeInTheDocument();
  expect(screen.getByText("Total return")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Backtest #100" })).toBeInTheDocument();
  const scrollRegion = document.querySelector(".walk-forward-window-scroll");
  expect(scrollRegion).not.toBeNull();
  expect((scrollRegion as HTMLElement).querySelector(".holdings-table")).not.toBeNull();
  expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(width);
});

it("never renders rolling or calendar stability metrics on the Walk-forward parent", async () => {
  detailMock.mockResolvedValue(detail);

  render(<WalkForwardDetailPage runId="42" />);

  await screen.findByText("Walk-forward #42");
  expect(screen.queryByText("Return stability")).not.toBeInTheDocument();
  expect(screen.queryByText("Rolling Return")).not.toBeInTheDocument();
  expect(screen.queryByText("Rolling Volatility")).not.toBeInTheDocument();
  expect(screen.queryByText("Rolling Sharpe")).not.toBeInTheDocument();
  expect(screen.queryByText("Monthly and yearly returns")).not.toBeInTheDocument();
  expect(screen.queryByText("63-session trailing window")).not.toBeInTheDocument();
  // Stitched reset semantics remain, and independent OOS links stay navigable.
  expect(screen.getByText(/No seam return, holdings carry/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Backtest #100" })).toBeInTheDocument();
});

it("keeps OOS detail links navigable when the stitched curve is unavailable", async () => {
  detailMock.mockResolvedValue({
    ...detail,
    stitched_oos: {
      status: "unavailable_non_contiguous_windows",
      initial_net_value: null,
      ending_net_value: null,
      total_return: null,
      points: []
    }
  });

  render(<WalkForwardDetailPage runId="42" />);

  await screen.findByText(/Gap or overlap windows/);
  expect(screen.queryByText("Return stability")).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Backtest #100" })).toBeInTheDocument();
});

const v3Detail: WalkForwardDetailResponse = {
  ...v2Detail,
  run: { ...v2Detail.run, evidence_version: "wf_evidence_v3" },
  evidence_version: "wf_evidence_v3",
  evidence: {
    ...(v2Detail.evidence as NonNullable<WalkForwardDetailResponse["evidence"]>),
    tail_distribution: {
      per_window: [
        {
          ordinal: 0,
          owners: {
            strategy: {
              historical_var_95: 0.02,
              historical_cvar_95: 0.06,
              return_skewness: 0.1,
              return_excess_kurtosis: 0.2,
              observation_count: 100,
              tail_observation_count: 5,
              evidence_status: "sufficient"
            },
            equal_weight_monthly: {
              historical_var_95: 0.01,
              historical_cvar_95: 0.03,
              return_skewness: -0.1,
              return_excess_kurtosis: 0.1,
              observation_count: 100,
              tail_observation_count: 5,
              evidence_status: "sufficient"
            },
            csi_300_buy_hold: {
              historical_var_95: 0.04,
              historical_cvar_95: 0.08,
              return_skewness: 0.2,
              return_excess_kurtosis: -0.3,
              observation_count: 100,
              tail_observation_count: 5,
              evidence_status: "sufficient"
            }
          }
        },
        {
          ordinal: 1,
          owners: {
            strategy: {
              historical_var_95: null,
              historical_cvar_95: null,
              return_skewness: null,
              return_excess_kurtosis: null,
              observation_count: 99,
              tail_observation_count: 5,
              evidence_status: "insufficient_evidence"
            },
            equal_weight_monthly: {
              historical_var_95: 0,
              historical_cvar_95: 0,
              return_skewness: null,
              return_excess_kurtosis: null,
              observation_count: 100,
              tail_observation_count: 5,
              evidence_status: "sufficient"
            },
            csi_300_buy_hold: {
              historical_var_95: 0.05,
              historical_cvar_95: 0.09,
              return_skewness: 0.3,
              return_excess_kurtosis: -0.4,
              observation_count: 100,
              tail_observation_count: 5,
              evidence_status: "sufficient"
            }
          }
        }
      ],
      aggregates: {
        strategy: {
          historical_var_95: metric(0.02),
          historical_cvar_95: metric(0.06),
          return_skewness: metric(0.1),
          return_excess_kurtosis: metric(0.2)
        },
        equal_weight_monthly: {
          historical_var_95: metric(0.01),
          historical_cvar_95: metric(0.03),
          return_skewness: metric(-0.1),
          return_excess_kurtosis: metric(0.1)
        },
        csi_300_buy_hold: {
          historical_var_95: metric(0.045),
          historical_cvar_95: metric(0.085),
          return_skewness: metric(0.25),
          return_excess_kurtosis: metric(-0.35)
        }
      }
    }
  }
};

it("presents v3 per-window and aggregate distribution evidence with owner-specific counts", async () => {
  detailMock.mockResolvedValue(v3Detail);

  render(<WalkForwardDetailPage runId="42" />);

  await screen.findByRole("heading", { name: "One-day historical distribution risk (95%)" });
  expect(
    screen.getByText(/descriptive statistics across independent per-window metric estimates/i)
  ).toBeInTheDocument();
  // Aggregate owner groups.
  expect(screen.getByRole("heading", { name: "Strategy" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Equal-weight monthly" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "CSI 300 buy-and-hold" })).toBeInTheDocument();
  // Per-window exact values and null/status handling.
  const table = screen.getByRole("table", { name: /Persisted one-day historical distribution evidence/ });
  expect(within(table).getAllByText("0.020000")).toHaveLength(1);
  expect(within(table).getAllByText("0.060000")).toHaveLength(1);
  expect(within(table).getAllByText("0.040000")).toHaveLength(1);
  expect(within(table).getAllByText("n/a")).toHaveLength(6);
  expect(within(table).getAllByText("99")).toHaveLength(1);
  expect(within(table).getAllByText("insufficient_evidence")).toHaveLength(1);
  expect(within(table).getAllByText("sufficient")).toHaveLength(5);
  expect(within(table).getAllByText("0.000000")).toHaveLength(2);
  // Existing v2/benchmark-regime and navigation content is preserved.
  expect(screen.getByText("CSI 300 ETF proxy Alpha (252D compounded)")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Backtest #100" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Stitched OOS capital path" })).toBeInTheDocument();
});

it("does not claim a combined-distribution risk value or pass/fail verdicts", async () => {
  detailMock.mockResolvedValue(v3Detail);

  render(<WalkForwardDetailPage runId="42" />);

  await screen.findByRole("heading", { name: "One-day historical distribution risk (95%)" });
  expect(screen.queryByText(/combined return distribution/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/worst/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/pass/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/fail/i)).not.toBeInTheDocument();
});

it.each([
  [1440, 1000],
  [390, 844]
])("keeps v3 distribution evidence and existing navigation readable without overflow at %ipx wide", async (width, height) => {
  Object.defineProperty(window, "innerWidth", { value: width, configurable: true, writable: true });
  Object.defineProperty(window, "innerHeight", { value: height, configurable: true, writable: true });
  detailMock.mockResolvedValue(v3Detail);

  render(<WalkForwardDetailPage runId="42" />);

  await screen.findByRole("heading", { name: "One-day historical distribution risk (95%)" });
  expect(screen.getByRole("heading", { name: "Per-window evidence" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Backtest #100" })).toBeInTheDocument();
  expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(width);
});
