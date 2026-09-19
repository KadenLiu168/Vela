import { describe, expect, it } from "vitest";
import type {
  DashboardBacktestSummary,
  DashboardResponse,
  DashboardWalkForwardOos,
  DashboardWalkForwardSummary
} from "../api/client";
import {
  calendarDaysBetween,
  deriveOosHeadlines,
  derivePerformanceEvidence,
  deriveResearchFacts,
  describeOosAvailability,
  describeWalkForwardState,
  RESEARCH_ACTION_TARGET_IDS,
  selectNextResearchAction,
  walkForwardStatusLabel
} from "./researchWorkbench";

function dashboard(overrides: Partial<DashboardResponse> = {}): DashboardResponse {
  return {
    strategy: {
      strategy_id: "Dual_momentum",
      version: "v1",
      universe_config: "config/etf_pool.yaml",
      costs: { transaction_cost_bps: 10 },
      performance: {},
      rebalance: { frequency: "weekly" },
      type: "equal_weight",
      parameters: {}
    },
    market_data: {
      price_rows: 100,
      covered_etfs: 2,
      earliest_trade_date: "2024-01-01",
      latest_trade_date: "2024-12-31",
      etf_list: []
    },
    latest_signal: null,
    recent_backtest: null,
    latest_walk_forward: null,
    recent_fetch_logs: [],
    ...overrides
  };
}

function backtest(overrides: Partial<DashboardBacktestSummary> = {}): DashboardBacktestSummary {
  return {
    run_id: 1,
    strategy_id: "Dual_momentum",
    config_version: "v1",
    start_date: "2019-01-01",
    end_date: "2024-12-31",
    status: "success",
    total_return: "-0.173422",
    annualized_return: "-0.031245",
    max_drawdown: "-0.418520",
    sharpe_ratio: "-0.154367",
    started_at: "2026-08-12T03:11:57",
    benchmarks: [],
    ...overrides
  };
}

describe("calendarDaysBetween", () => {
  it("counts whole calendar days across month boundaries", () => {
    expect(calendarDaysBetween("2024-12-31", "2025-01-01")).toBe(1);
    expect(calendarDaysBetween("2024-01-01", "2024-12-31")).toBe(365);
  });

  it("returns a negative count when the first date is later", () => {
    expect(calendarDaysBetween("2025-01-01", "2024-12-31")).toBe(-1);
  });

  it("returns null for non-date input", () => {
    expect(calendarDaysBetween("not-a-date", "2024-12-31")).toBeNull();
  });
});

describe("deriveResearchFacts", () => {
  it("reports the stored data cutoff and missing artifacts", () => {
    const facts = deriveResearchFacts(dashboard());

    expect(facts.map((fact) => fact.key)).toEqual([
      "market_data",
      "signal",
      "backtest",
      "walk_forward"
    ]);
    expect(facts[0].value).toBe("Stored through 2024-12-31");
    expect(facts[0].isMissing).toBe(false);
    expect(facts[1].value).toBe("No successful signal");
    expect(facts[1].isMissing).toBe(true);
    expect(facts[2].value).toBe("No backtest run");
    expect(facts[3].value).toBe("No run yet");
  });

  it("states that no price rows are stored instead of a cutoff", () => {
    const facts = deriveResearchFacts(
      dashboard({
        market_data: {
          price_rows: 0,
          covered_etfs: 0,
          earliest_trade_date: null,
          latest_trade_date: null,
          etf_list: []
        }
      })
    );

    expect(facts[0].value).toBe("No price rows stored");
    expect(facts[0].isMissing).toBe(true);
  });

  it("measures how far an artifact trails the stored market data in calendar days", () => {
    const facts = deriveResearchFacts(
      dashboard({
        latest_signal: {
          signal_id: 307,
          signal_date: "2024-12-31",
          config_version: "v1",
          status: "success",
          result: "rebalance",
          generated_at: "2026-08-12T03:11:57",
          is_fallback: false,
          position_count: 2,
          source: "manual",
          backtest_run_id: null,
          positions: []
        },
        recent_backtest: backtest({ end_date: "2024-06-30" })
      })
    );

    expect(facts[1].lagCalendarDays).toBeNull();
    expect(facts[2].lagCalendarDays).toBe(184);
  });

  it("does not call an artifact current artifact lagging", () => {
    const facts = deriveResearchFacts(
      dashboard({
        latest_signal: {
          signal_id: 307,
          signal_date: "2024-12-31",
          config_version: "v1",
          status: "success",
          result: "rebalance",
          generated_at: "2026-08-12T03:11:57",
          is_fallback: false,
          position_count: 2,
          source: "manual",
          backtest_run_id: null,
          positions: []
        }
      })
    );

    expect(facts[1].lagCalendarDays).toBeNull();
  });

  it("leaves no cutoff to compare when no price rows are stored", () => {
    const facts = deriveResearchFacts(
      dashboard({
        market_data: {
          price_rows: 0,
          covered_etfs: 0,
          earliest_trade_date: null,
          latest_trade_date: null,
          etf_list: []
        },
        latest_signal: {
          signal_id: 307,
          signal_date: "2024-12-31",
          config_version: "v1",
          status: "success",
          result: "rebalance",
          generated_at: "2026-08-12T03:11:57",
          is_fallback: false,
          position_count: 2,
          source: "manual",
          backtest_run_id: null,
          positions: []
        }
      })
    );

    expect(facts[1].lagCalendarDays).toBeNull();
  });
});

describe("selectNextResearchAction", () => {
  it("asks for market data first when none is stored", () => {
    const empty = dashboard({
      market_data: {
        price_rows: 0,
        covered_etfs: 0,
        earliest_trade_date: null,
        latest_trade_date: null,
        etf_list: []
      }
    });

    expect(selectNextResearchAction(empty, deriveResearchFacts(empty))).toEqual({
      label: "Fetch market data",
      targetId: RESEARCH_ACTION_TARGET_IDS.fetchMarketData
    });
  });

  it("asks for a signal when none exists but data is stored", () => {
    const withoutSignal = dashboard();

    expect(selectNextResearchAction(withoutSignal, deriveResearchFacts(withoutSignal))).toEqual({
      label: "Generate signal",
      targetId: RESEARCH_ACTION_TARGET_IDS.generateSignal
    });
  });

  it("asks for a signal when the signal trails the stored data", () => {
    const staleSignal = dashboard({
      latest_signal: {
        signal_id: 307,
        signal_date: "2024-06-30",
        config_version: "v1",
        status: "success",
        result: "rebalance",
        generated_at: "2026-08-12T03:11:57",
        is_fallback: false,
        position_count: 2,
        source: "manual",
        backtest_run_id: null,
        positions: []
      }
    });

    expect(selectNextResearchAction(staleSignal, deriveResearchFacts(staleSignal))).toEqual({
      label: "Generate signal",
      targetId: RESEARCH_ACTION_TARGET_IDS.generateSignal
    });
  });

  it("asks for a backtest when data and a current signal exist but no run does", () => {
    const current = dashboard({
      latest_signal: {
        signal_id: 307,
        signal_date: "2024-12-31",
        config_version: "v1",
        status: "success",
        result: "rebalance",
        generated_at: "2026-08-12T03:11:57",
        is_fallback: false,
        position_count: 2,
        source: "manual",
        backtest_run_id: null,
        positions: []
      }
    });

    expect(selectNextResearchAction(current, deriveResearchFacts(current))).toEqual({
      label: "Run a backtest",
      targetId: RESEARCH_ACTION_TARGET_IDS.runBacktest
    });
  });

  it("offers no action once data, signal and backtest are all current", () => {
    const current = dashboard({
      latest_signal: {
        signal_id: 307,
        signal_date: "2024-12-31",
        config_version: "v1",
        status: "success",
        result: "rebalance",
        generated_at: "2026-08-12T03:11:57",
        is_fallback: false,
        position_count: 2,
        source: "manual",
        backtest_run_id: null,
        positions: []
      },
      recent_backtest: backtest({ end_date: "2024-12-31" })
    });

    expect(selectNextResearchAction(current, deriveResearchFacts(current))).toBeNull();
  });

  it("does not treat a historical backtest range as an action trigger", () => {
    const shortRange = dashboard({
      latest_signal: {
        signal_id: 307,
        signal_date: "2024-12-31",
        config_version: "v1",
        status: "success",
        result: "rebalance",
        generated_at: "2026-08-12T03:11:57",
        is_fallback: false,
        position_count: 2,
        source: "manual",
        backtest_run_id: null,
        positions: []
      },
      recent_backtest: backtest({ end_date: "2020-12-31" })
    });

    expect(selectNextResearchAction(shortRange, deriveResearchFacts(shortRange))).toBeNull();
  });
});

describe("walk-forward state labels", () => {
  it("labels every persisted status", () => {
    expect(walkForwardStatusLabel("queued")).toBe("Queued");
    expect(walkForwardStatusLabel("running")).toBe("Running");
    expect(walkForwardStatusLabel("success")).toBe("Completed");
    expect(walkForwardStatusLabel("failed")).toBe("Failed");
  });

  it("includes the window count when windows were persisted", () => {
    expect(
      describeWalkForwardState({
        run_id: 1,
        strategy_id: "Dual_momentum",
        status: "success",
        start_date: "2019-01-01",
        end_date: "2024-12-31",
        window_count: 5,
        finished_at: "2026-08-12T03:11:57",
        error_message: null,
        oos: null
      })
    ).toBe("Completed · 5 windows");
  });

  it("states that no run exists yet", () => {
    expect(describeWalkForwardState(null)).toBe("No run yet");
  });
});

describe("derivePerformanceEvidence", () => {
  it("uses the CSI 300 buy-and-hold benchmark as primary and published differences", () => {
    const evidence = derivePerformanceEvidence(
      backtest({
        benchmarks: [
          {
            key: "equal_weight_monthly",
            name: "Equal-weight monthly rebalanced portfolio",
            total_return: "0.812893",
            total_return_difference: "-0.986315",
            annualized_return_difference: "-0.135481",
            sharpe_ratio: "0.714051",
            max_drawdown: "-0.185086"
          },
          {
            key: "csi_300_buy_hold",
            name: "CSI 300 buy-and-hold",
            total_return: "0.427400",
            total_return_difference: "-0.600822",
            annualized_return_difference: "-0.092348",
            sharpe_ratio: "0.322564",
            max_drawdown: "-0.384516"
          }
        ]
      })
    );

    expect(evidence.primaryBenchmarkName).toBe("CSI 300 buy-and-hold");
    expect(evidence.headlines).toEqual([
      { key: "total_return", label: "Total return", value: "-17.34%", difference: "-60.08%" },
      {
        key: "annualized_return",
        label: "CAGR (calendar-time)",
        value: "-3.12%",
        difference: "-9.23%"
      },
      {
        key: "sharpe_ratio",
        label: "Sharpe (daily returns, 252D)",
        value: "-0.15",
        difference: "-0.48"
      },
      {
        key: "max_drawdown",
        label: "Max drawdown",
        value: "-41.85%",
        difference: "deeper by 3.40%"
      }
    ]);
  });

  it("leaves differences unavailable for a run without benchmarks", () => {
    const evidence = derivePerformanceEvidence(backtest());

    expect(evidence.primaryBenchmarkName).toBeNull();
    expect(evidence.headlines.every((headline) => headline.difference === null)).toBe(true);
  });

  it("does not fabricate a difference when a benchmark value is missing", () => {
    const evidence = derivePerformanceEvidence(
      backtest({
        benchmarks: [
          {
            key: "csi_300_buy_hold",
            name: "CSI 300 buy-and-hold",
            total_return: null,
            total_return_difference: null,
            annualized_return_difference: null,
            sharpe_ratio: null,
            max_drawdown: null
          }
        ]
      })
    );

    expect(evidence.headlines[0].difference).toBe("n/a");
    expect(evidence.headlines[2].difference).toBe("n/a");
    expect(evidence.headlines[3].difference).toBe("n/a");
  });
});

const oosEvidence: DashboardWalkForwardOos = {
  metrics: {
    total_return: {
      median: 0.041,
      mean: 0.038,
      window_count: 5,
      valid_count: 5,
      evidence_status: "sufficient"
    },
    sharpe_ratio: {
      median: 0.62,
      mean: 0.58,
      window_count: 5,
      valid_count: 4,
      evidence_status: "sufficient"
    },
    max_drawdown: {
      median: -0.118,
      mean: -0.121,
      window_count: 5,
      valid_count: 5,
      evidence_status: "sufficient"
    }
  },
  positive_window_rate: {
    value: 0.6,
    numerator: 3,
    denominator: 5,
    window_count: 5,
    valid_count: 5,
    evidence_status: "sufficient"
  },
  generalization_gap: {
    median: 0.21,
    mean: 0.2,
    window_count: 5,
    valid_count: 5,
    evidence_status: "sufficient"
  },
  benchmarks: {
    equal_weight_monthly: {
      outperformance_rate: {
        value: 0.4,
        numerator: 2,
        denominator: 5,
        window_count: 5,
        valid_count: 5,
        evidence_status: "sufficient"
      }
    },
    csi_300_buy_hold: {
      outperformance_rate: {
        value: 0.5,
        numerator: 2,
        denominator: 4,
        window_count: 5,
        valid_count: 4,
        evidence_status: "sufficient"
      }
    }
  }
};

describe("deriveOosHeadlines", () => {
  it("renders each headline from its persisted evidence field", () => {
    const headlines = deriveOosHeadlines(oosEvidence);

    expect(headlines).toEqual([
      { label: "OOS total return", value: "4.10%", meta: "median · mean 3.80%" },
      { label: "OOS median Sharpe", value: "0.62", meta: "4/5 valid windows" },
      {
        label: "OOS max drawdown",
        value: "-11.80%",
        meta: "median across 5 windows"
      },
      { label: "Positive window rate", value: "60.00%", meta: "3/5 windows" },
      {
        label: "Benchmark outperformance",
        value: "50.00%",
        meta: "vs CSI 300 buy-and-hold · 2/4 windows"
      }
    ]);
  });

  it("marks outperformance unavailable without a benchmark", () => {
    const headlines = deriveOosHeadlines({ ...oosEvidence, benchmarks: {} });

    expect(headlines[4]).toEqual({
      label: "Benchmark outperformance",
      value: "n/a",
      meta: "No benchmark evidence"
    });
  });

  it("renders n/a instead of zero for a null aggregate", () => {
    const headlines = deriveOosHeadlines({
      ...oosEvidence,
      metrics: {
        ...oosEvidence.metrics,
        sharpe_ratio: {
          median: null,
          mean: null,
          window_count: 5,
          valid_count: 0,
          evidence_status: "insufficient_evidence"
        }
      }
    });

    expect(headlines[1].value).toBe("n/a");
  });
});

describe("describeOosAvailability", () => {
  const summary = (overrides: Partial<DashboardWalkForwardSummary>): DashboardWalkForwardSummary => ({
    run_id: 1,
    strategy_id: "Dual_momentum",
    status: "queued",
    start_date: "2019-01-01",
    end_date: "2024-12-31",
    window_count: 0,
    finished_at: null,
    error_message: null,
    oos: null,
    ...overrides
  });

  it("states the non-terminal status", () => {
    expect(describeOosAvailability(summary({ status: "running" }))).toBe(
      "Evidence is unavailable until this running run reaches a terminal state."
    );
  });

  it("states that a failed run is why evidence is unavailable", () => {
    expect(describeOosAvailability(summary({ status: "failed" }))).toBe(
      "Evidence is unavailable because this run failed."
    );
  });

  it("surfaces the API error message for a failed run", () => {
    expect(
      describeOosAvailability(summary({ status: "failed", error_message: "missing market data" }))
    ).toBe("Evidence is unavailable because this run failed: missing market data");
  });
});
