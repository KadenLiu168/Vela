/*
 * In-memory API fixtures for the acceptance workflow.
 *
 * Data is deterministic and exercised through method/path/query-exact
 * matching (see support/network.ts). Shapes mirror the API client types;
 * fixtures deliberately include long mixed Chinese/Latin names, negative
 * values, nulls and a three-series equity curve (strategy + two benchmarks)
 * per the acceptance matrix.
 */
import type { ApiFixtureSpec } from "../support/network";

const benchmark = (key: string, name: string, overrides: Record<string, unknown> = {}) => ({
  key,
  name,
  total_return: "0.081234",
  annualized_return: "0.152345",
  max_drawdown: "-0.076543",
  volatility: "0.112345",
  sharpe_ratio: "0.912345",
  sortino_ratio: "1.234567",
  calmar_ratio: "1.876543",
  longest_drawdown_duration_sessions: 4,
  longest_drawdown_peak_date: "2026-01-12",
  longest_drawdown_trough_date: "2026-01-19",
  longest_drawdown_recovery_date: "2026-02-03",
  tracking_error: "0.034567",
  information_ratio: "1.123456",
  total_return_difference: "0.038766",
  annualized_return_difference: "0.007655",
  capm_alpha: "0.012345",
  capm_beta: "0.987654",
  capm_r_squared: "0.765432",
  capm_observation_count: 120,
  up_capture_ratio: "1.012345",
  up_capture_observation_count: 60,
  down_capture_ratio: "0.912345",
  down_capture_observation_count: 60,
  equity_curve: [],
  historical_var_95: "-0.012345",
  historical_cvar_95: "-0.023456",
  return_skewness: "-0.123456",
  return_excess_kurtosis: "0.234567",
  distribution_observation_count: 120,
  tail_observation_count: 6,
  distribution_evidence_status: "available",
  ...overrides
});

const returnStability = {
  strategy: {
    window_sessions: 63,
    rolling_status: "available",
    sharpe_status: "available",
    source_point_count: 6,
    effective_return_count: 5,
    rolling: [
      { window_end: "2026-01-12", sharpe_ratio: "1.234567", annualized_return: "0.245678", max_drawdown: "-0.054321", observation_count: 3 },
      { window_end: "2026-01-17", sharpe_ratio: "1.054321", annualized_return: "0.223456", max_drawdown: "-0.065432", observation_count: 4 }
    ],
    monthly: [
      { period: "2026-01", first_date: "2026-01-02", last_date: "2026-01-27", observation_count: 6, total_return: "0.054321", is_partial: false }
    ],
    yearly: [
      { period: "2026", first_date: "2026-01-02", last_date: "2026-01-27", observation_count: 6, total_return: "0.154321", is_partial: true }
    ]
  },
  benchmarks: [
    {
      key: "equal_weight_monthly",
      name: "Equal-weight monthly rebalanced portfolio",
      window_sessions: 63,
      rolling_status: "available",
      sharpe_status: "available",
      source_point_count: 6,
      effective_return_count: 5,
      rolling: [
        { window_end: "2026-01-12", sharpe_ratio: "0.987654", annualized_return: "0.187654", max_drawdown: "-0.043210", observation_count: 3 }
      ],
      monthly: [
        { period: "2026-01", first_date: "2026-01-02", last_date: "2026-01-27", observation_count: 6, total_return: "0.032109", is_partial: false }
      ],
      yearly: [
        { period: "2026", first_date: "2026-01-02", last_date: "2026-01-27", observation_count: 6, total_return: "0.098765", is_partial: true }
      ]
    }
  ]
};

export const dashboardResponse = {
  strategy: {
    strategy_id: "dual_momentum",
    version: "v1",
    type: "dual_momentum",
    universe_config: "config/etf_pool.yaml",
    parameters: {
      momentum: { short_window_days: 63, long_window_days: 126 },
      score_weights: { short: 0.4, long: 0.6 },
      trend_filter: { moving_average_days: 120, price_relation: "above" },
      selection: { top_n: 2 },
      defense: { assets: [{ exchange: "SSE", symbol: "511010" }] }
    },
    costs: { transaction_cost_bps: 10 },
    performance: { risk_free_rate: 0.02 },
    rebalance: { frequency: "weekly" }
  },
  market_data: {
    price_rows: 1200,
    covered_etfs: 8,
    earliest_trade_date: "2025-01-02",
    latest_trade_date: "2026-06-23",
    etf_list: [
      {
        etf_id: 1,
        exchange: "SSE",
        symbol: "510300",
        name: "华泰柏瑞沪深300交易型开放式指数证券投资基金",
        category: "equity_cn_broad",
        earliest_trade_date: "2025-01-02"
      },
      {
        etf_id: 2,
        exchange: "SZSE",
        symbol: "159915",
        name: "易方达创业板交易型开放式指数证券投资基金",
        category: "equity_cn_growth",
        earliest_trade_date: "2025-01-02"
      },
      {
        etf_id: 3,
        exchange: "SSE",
        symbol: "511010",
        name: "国债ETF",
        category: "bond_cn",
        earliest_trade_date: "2025-01-02"
      }
    ]
  },
  latest_signal: {
    signal_id: 42,
    signal_date: "2026-06-23",
    config_version: "v1",
    status: "success",
    result: "rebalance",
    generated_at: "2026-06-23T09:30:00",
    is_fallback: false,
    position_count: 2,
    source: "manual",
    backtest_run_id: null,
    positions: [
      {
        exchange: "SSE",
        symbol: "510300",
        name: "华泰柏瑞沪深300交易型开放式指数证券投资基金",
        target_weight: "0.500000",
        rank: 1,
        score: "0.812345",
        is_fallback: false
      },
      {
        exchange: "SZSE",
        symbol: "159915",
        name: "易方达创业板交易型开放式指数证券投资基金",
        target_weight: "0.500000",
        rank: 2,
        score: "0.654321",
        is_fallback: false
      }
    ]
  },
  recent_backtest: {
    run_id: 7,
    strategy_id: "dual_momentum",
    config_version: "v1",
    start_date: "2026-01-01",
    end_date: "2026-06-01",
    status: "success",
    total_return: "0.154321",
    annualized_return: "0.312345",
    max_drawdown: "-0.076543",
    sharpe_ratio: "1.234567",
    started_at: "2026-06-02T09:00:00",
    benchmarks: [
      {
        key: "equal_weight_monthly",
        name: "Equal-weight monthly rebalanced portfolio",
        total_return: "0.115555",
        total_return_difference: "0.038766",
        annualized_return_difference: "0.007655",
        sharpe_ratio: "0.987654",
        max_drawdown: "-0.043210"
      },
      {
        key: "csi_300_buy_hold",
        name: "CSI 300 buy-and-hold",
        total_return: "0.045678",
        total_return_difference: "0.108643",
        annualized_return_difference: "0.223333",
        sharpe_ratio: "0.712345",
        max_drawdown: "-0.101234"
      }
    ]
  },
  latest_walk_forward: {
    run_id: 3,
    strategy_id: "dual_momentum",
    start_date: "2026-01-01",
    end_date: "2026-12-31",
    window_count: 4,
    provenance_version: "wf_provenance_v1",
    evidence_version: "wf_evidence_v1",
    status: "success",
    error_message: null,
    started_at: "2026-12-01T00:00:00",
    finished_at: "2026-12-02T00:00:00",
    oos: {
      metrics: {
        total_return: { median: 0.12, mean: 0.1, window_count: 4, valid_count: 4, evidence_status: "sufficient" },
        sharpe_ratio: { median: 1.05, mean: 1.02, window_count: 4, valid_count: 4, evidence_status: "sufficient" },
        max_drawdown: { median: -0.18, mean: -0.17, window_count: 4, valid_count: 4, evidence_status: "sufficient" }
      },
      positive_window_rate: {
        value: 0.75,
        numerator: 3,
        denominator: 4,
        window_count: 4,
        valid_count: 4,
        evidence_status: "sufficient"
      },
      generalization_gap: { median: 0.03, mean: 0.03, window_count: 4, valid_count: 4, evidence_status: "sufficient" },
      benchmarks: {
        equal_weight_monthly: {
          outperformance_rate: {
            value: 0.5,
            numerator: 2,
            denominator: 4,
            window_count: 4,
            valid_count: 4,
            evidence_status: "sufficient"
          }
        },
        csi_300_buy_hold: {
          outperformance_rate: {
            value: 0.75,
            numerator: 3,
            denominator: 4,
            window_count: 4,
            valid_count: 4,
            evidence_status: "sufficient"
          }
        }
      }
    }
  },
  recent_fetch_logs: [
    {
      fetch_log_id: 11,
      fetch_time: "2026-06-24T08:00:00",
      mode: "incremental",
      status: "partial",
      rows_fetched: 25,
      rows_inserted: 20,
      rows_updated: 5,
      error_summary: "QQQ: provider timeout"
    },
    {
      fetch_log_id: 10,
      fetch_time: "2026-06-23T07:05:00",
      mode: "full",
      status: "success",
      rows_fetched: 200,
      rows_inserted: 180,
      rows_updated: 20,
      error_summary: null
    }
  ]
};

export const signalDetailResponse = {
  signal: {
    signal_id: 42,
    signal_date: "2026-06-23",
    strategy_id: "dual_momentum",
    config_version: "v1",
    generated_at: "2026-06-23T09:30:00",
    result: "rebalance",
    is_fallback: false,
    source: "manual",
    backtest_run_id: null
  },
  positions: [
    {
      exchange: "SSE",
      symbol: "510300",
      name: "华泰柏瑞沪深300交易型开放式指数证券投资基金",
      target_weight: "0.333333",
      rank: 1,
      score: "0.812345",
      is_fallback: false
    },
    {
      exchange: "SZSE",
      symbol: "159915",
      name: "易方达创业板交易型开放式指数证券投资基金",
      target_weight: "0.333333",
      rank: 2,
      score: null,
      is_fallback: true
    },
    {
      exchange: "SSE",
      symbol: "511010",
      name: "国债ETF",
      target_weight: "0.333334",
      rank: null,
      score: "-0.123456",
      is_fallback: false
    }
  ]
};

export const signalListResponse = {
  signals: [
    {
      signal_id: 42,
      signal_date: "2026-06-23",
      config_version: "v1",
      generated_at: "2026-06-23T09:30:00",
      result: "rebalance",
      is_fallback: false,
      position_count: 3,
      source: "manual",
      backtest_run_id: null
    },
    {
      signal_id: 41,
      signal_date: "2026-06-20",
      config_version: "v1",
      generated_at: "2026-06-20T09:30:00",
      result: "hold",
      is_fallback: true,
      position_count: 0,
      source: "backtest",
      backtest_run_id: 7
    },
    {
      signal_id: 40,
      signal_date: "2026-06-15",
      config_version: "v1",
      generated_at: "2026-06-15T09:30:00",
      result: null,
      is_fallback: false,
      position_count: 2,
      source: "scheduled",
      backtest_run_id: null
    }
  ]
};

export const backtestListResponse = {
  runs: [
    {
      run_id: 7,
      strategy_id: "dual_momentum",
      config_version: "v1",
      start_date: "2026-01-01",
      end_date: "2026-06-01",
      status: "success",
      started_at: "2026-06-02T09:00:00",
      finished_at: "2026-06-02T09:05:00",
      total_return: "0.154321",
      annualized_return: "0.312345",
      max_drawdown: "-0.076543",
      volatility: "0.112345",
      sharpe_ratio: "1.234567"
    },
    {
      run_id: 6,
      strategy_id: "dual_momentum",
      config_version: "v1",
      start_date: "2025-07-01",
      end_date: "2025-12-31",
      status: "failed",
      started_at: "2026-01-02T09:00:00",
      finished_at: "2026-01-02T09:00:10",
      total_return: null,
      annualized_return: null,
      max_drawdown: null,
      volatility: null,
      sharpe_ratio: null
    }
  ],
  total: 2,
  limit: 10,
  offset: 0
};

/** Three plotted series: strategy + two benchmarks with distinct values. */
export const backtestDetailResponse = {
  run: {
    run_id: 7,
    strategy_id: "dual_momentum",
    config_version: "v1",
    start_date: "2026-01-01",
    end_date: "2026-06-01",
    parameters_json: '{"top_n": 2, "momentum": {"short_window_days": 63, "long_window_days": 126}}',
    status: "success",
    error_message: null,
    started_at: "2026-06-02T09:00:00",
    finished_at: "2026-06-02T09:05:00"
  },
  metrics: {
    total_return: "0.154321",
    annualized_return: "0.312345",
    max_drawdown: "-0.076543",
    volatility: "0.112345",
    sharpe_ratio: "1.234567"
  },
  equity_curve: [
    { trade_date: "2026-01-02", net_value: "1.000000", cash: "100.000000", market_value: "9900.000000", total_assets: "10000.000000", positions_json: "[]" },
    { trade_date: "2026-01-09", net_value: "1.020000", cash: "100.000000", market_value: "10100.000000", total_assets: "10200.000000", positions_json: "[]" },
    { trade_date: "2026-01-16", net_value: "0.986000", cash: "100.000000", market_value: "9760.000000", total_assets: "9860.000000", positions_json: "[]" },
    { trade_date: "2026-01-23", net_value: "1.043000", cash: "100.000000", market_value: "10320.000000", total_assets: "10420.000000", positions_json: "[]" },
    { trade_date: "2026-01-30", net_value: "1.088000", cash: "100.000000", market_value: "10780.000000", total_assets: "10880.000000", positions_json: "[]" },
    { trade_date: "2026-02-06", net_value: "1.154321", cash: "100.000000", market_value: "11432.100000", total_assets: "11532.100000", positions_json: "[]" }
  ],
  benchmarks: [
    benchmark("equal_weight_monthly", "Equal-weight monthly rebalanced portfolio", {
      equity_curve: [
        { trade_date: "2026-01-02", net_value: "1.000000" },
        { trade_date: "2026-01-09", net_value: "1.012000" },
        { trade_date: "2026-01-16", net_value: "0.991000" },
        { trade_date: "2026-01-23", net_value: "1.023000" },
        { trade_date: "2026-01-30", net_value: "1.041000" },
        { trade_date: "2026-02-06", net_value: "1.115555" }
      ]
    }),
    benchmark("csi_300_buy_hold", "CSI 300 buy-and-hold", {
      equity_curve: [
        { trade_date: "2026-01-02", net_value: "1.000000" },
        { trade_date: "2026-01-09", net_value: "1.008000" },
        { trade_date: "2026-01-16", net_value: "0.972000" },
        { trade_date: "2026-01-23", net_value: "0.998000" },
        { trade_date: "2026-01-30", net_value: "1.011000" },
        { trade_date: "2026-02-06", net_value: "1.045678" }
      ]
    })
  ],
  signal_ids: [7, 9],
  signal_count: 2,
  return_stability: returnStability
};

export const backtestSignalsResponse = {
  signals: [
    { signal_id: 7, signal_date: "2026-01-05", result: "rebalance", backtest_run_id: 7 },
    { signal_id: 9, signal_date: "2026-02-02", result: null, backtest_run_id: 7 }
  ]
};

export const etfPriceTrendResponse = {
  etf: { id: 1, exchange: "SSE", symbol: "510300", name: "华泰柏瑞沪深300交易型开放式指数证券投资基金" },
  points: [
    { trade_date: "2026-01-02", price: "3.9120" },
    { trade_date: "2026-02-02", price: "4.0125" },
    { trade_date: "2026-03-02", price: "3.8450" },
    { trade_date: "2026-04-02", price: "4.1000" },
    { trade_date: "2026-05-02", price: "3.9700" }
  ]
};

const walkForwardMetric = (value: number | null) => ({
  mean: value,
  median: value,
  min: value === null ? null : value * 0.8,
  max: value === null ? null : value * 1.2,
  std: value === null ? null : 0.01,
  window_count: 4,
  valid_count: value === null ? 0 : 4,
  evidence_status: "sufficient"
});

export const walkForwardListResponse = {
  runs: [
    {
      run_id: 3,
      strategy_id: "dual_momentum",
      start_date: "2026-01-01",
      end_date: "2026-12-31",
      window_count: 4,
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
      finished_at: "2026-12-02T00:00:00"
    },
    {
      run_id: 4,
      strategy_id: "dual_momentum",
      start_date: "2026-01-01",
      end_date: "2026-12-31",
      window_count: 0,
      provenance_version: "wf_provenance_v1",
      evidence_version: "wf_evidence_v1",
      config_checksum: "c".repeat(64),
      input_data_checksum: "d".repeat(64),
      status: "queued",
      error_message: null,
      attempt_count: 0,
      claimed_at: null,
      heartbeat_at: null,
      lease_expires_at: null,
      started_at: "2026-12-02T00:00:00",
      finished_at: null
    }
  ],
  total: 2,
  limit: 10,
  offset: 0
};

export const walkForwardDetailResponse = {
  run: {
    run_id: 3,
    strategy_id: "dual_momentum",
    start_date: "2026-01-01",
    end_date: "2026-12-31",
    window_count: 4,
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
      total_return: walkForwardMetric(0.12),
      annualized_return: walkForwardMetric(0.08),
      max_drawdown: walkForwardMetric(-0.2),
      volatility: walkForwardMetric(0.15),
      sharpe_ratio: walkForwardMetric(1.1),
      sortino_ratio: walkForwardMetric(1.4),
      calmar_ratio: walkForwardMetric(0.5),
      longest_drawdown_duration_sessions: walkForwardMetric(8)
    },
    positive_window_rate: {
      numerator: 3,
      denominator: 4,
      value: 0.75,
      window_count: 4,
      valid_count: 4,
      evidence_status: "sufficient"
    },
    generalization_gap: walkForwardMetric(0.03),
    benchmarks: {
      equal_weight_monthly: {
        total_return_difference: walkForwardMetric(0.01),
        annualized_return_difference: walkForwardMetric(0.02),
        tracking_error: walkForwardMetric(0.04),
        information_ratio: walkForwardMetric(0.6),
        outperformance_rate: {
          numerator: 2,
          denominator: 4,
          value: 0.5,
          window_count: 4,
          valid_count: 4,
          evidence_status: "sufficient"
        }
      },
      csi_300_buy_hold: {
        total_return_difference: walkForwardMetric(0.02),
        annualized_return_difference: walkForwardMetric(0.03),
        tracking_error: walkForwardMetric(0.05),
        information_ratio: walkForwardMetric(0.7),
        outperformance_rate: {
          numerator: 3,
          denominator: 4,
          value: 0.75,
          window_count: 4,
          valid_count: 4,
          evidence_status: "sufficient"
        }
      }
    },
    parameter_stability: {
      lookback_days: {
        value_frequencies: { "120": 4 },
        transition_count: 0,
        comparison_count: 3,
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
            capm_alpha: null,
            capm_beta: null,
            capm_r_squared: null,
            capm_observation_count: null,
            up_capture_ratio: null,
            up_capture_observation_count: null,
            down_capture_ratio: null,
            down_capture_observation_count: null
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
            capm_alpha: null,
            capm_beta: null,
            capm_r_squared: null,
            capm_observation_count: null,
            up_capture_ratio: null,
            up_capture_observation_count: null,
            down_capture_ratio: null,
            down_capture_observation_count: null
          }
        ]
      }
    }
  ]
};

export const latestSignalResponse = {
  has_signal: true,
  signal: {
    signal_id: 42,
    signal_date: "2026-06-23",
    config_version: "v1",
    result: "rebalance",
    generated_at: "2026-06-23T09:30:00",
    is_fallback: false
  },
  positions: dashboardResponse.latest_signal.positions
};

/** The populated fixture set: every `/api` request a populated session issues. */
export function populatedFixtures(): ApiFixtureSpec[] {
  return [
    { method: "GET", path: "/api/health", body: { status: "ok" } },
    { method: "GET", path: "/api/dashboard", body: dashboardResponse },
    { method: "GET", path: "/api/backtests", query: { limit: "10", offset: "0" }, body: backtestListResponse },
    { method: "GET", path: "/api/backtests/{runId}", body: backtestDetailResponse },
    { method: "GET", path: "/api/backtests/{runId}/signals", query: { limit: "20", offset: "0" }, body: backtestSignalsResponse },
    { method: "GET", path: "/api/strategy-signals", query: { limit: "20", offset: "0" }, body: signalListResponse },
    { method: "GET", path: "/api/strategy-signals/latest", body: latestSignalResponse },
    { method: "GET", path: "/api/strategy-signals/{signalId}", body: signalDetailResponse },
    { method: "GET", path: "/api/walk-forwards", query: { limit: "10", offset: "0" }, body: walkForwardListResponse },
    { method: "GET", path: "/api/walk-forwards/{runId}", body: walkForwardDetailResponse },
    { method: "GET", path: "/api/etfs/{etfId}/prices", query: { range: "1y" }, body: etfPriceTrendResponse },
    { method: "GET", path: "/api/etfs/{etfId}/prices", query: { range: "3y" }, body: etfPriceTrendResponse },
    { method: "GET", path: "/api/etfs/{etfId}/prices", query: { range: "max" }, body: etfPriceTrendResponse },
    { method: "GET", path: "/api/etfs/{etfId}/prices", query: { range: "1m" }, body: etfPriceTrendResponse },
    { method: "GET", path: "/api/etfs/{etfId}/prices", query: { range: "3m" }, body: etfPriceTrendResponse }
  ];
}

/* ── State variants for the acceptance matrix ─────────────────────── */

/** Empty dashboard/list shapes reuse the same schemas with empty collections. */
export const emptyDashboardResponse = {
  ...dashboardResponse,
  latest_signal: null,
  recent_backtest: null,
  latest_walk_forward: null,
  recent_fetch_logs: [],
  market_data: {
    ...dashboardResponse.market_data,
    price_rows: 0,
    covered_etfs: 0,
    etf_list: []
  }
};

export const emptySignalListResponse = { signals: [] };
export const emptyBacktestListResponse = { runs: [], total: 0, limit: 10, offset: 0 };
export const emptyWalkForwardListResponse = {
  runs: [],
  total: 0,
  limit: 10,
  offset: 0
};

/** Legacy backtest detail: every benchmark/distribution field is null and
 *  evidence states report unavailable_legacy. */
export const legacyBacktestDetailResponse = {
  ...backtestDetailResponse,
  metrics: {
    total_return: null,
    annualized_return: null,
    max_drawdown: null,
    volatility: null,
    sharpe_ratio: null
  },
  equity_curve: [],
  benchmarks: [
    benchmark("equal_weight_monthly", "Equal-weight monthly rebalanced portfolio", {
      total_return: null,
      annualized_return: null,
      max_drawdown: null,
      volatility: null,
      sharpe_ratio: null,
      sortino_ratio: null,
      calmar_ratio: null,
      tracking_error: null,
      information_ratio: null,
      total_return_difference: null,
      annualized_return_difference: null,
      capm_alpha: null,
      capm_beta: null,
      capm_r_squared: null,
      up_capture_ratio: null,
      down_capture_ratio: null,
      historical_var_95: null,
      historical_cvar_95: null,
      return_skewness: null,
      return_excess_kurtosis: null,
      distribution_observation_count: null,
      tail_observation_count: null,
      distribution_evidence_status: "unavailable_legacy",
      equity_curve: []
    })
  ],
  return_stability: {
    strategy: {
      ...returnStability.strategy,
      rolling_status: "insufficient_observations",
      sharpe_status: "insufficient_observations",
      rolling: [],
      monthly: [],
      yearly: []
    },
    benchmarks: []
  }
};

/** Failed backtest run: the run reports a failure with an error message. */
export const failedBacktestDetailResponse = {
  ...backtestDetailResponse,
  run: {
    ...backtestDetailResponse.run,
    status: "failed",
    error_message: "Momentum computation failed for the requested range."
  },
  metrics: {
    total_return: null,
    annualized_return: null,
    max_drawdown: null,
    volatility: null,
    sharpe_ratio: null
  }
};

/** Queued walk-forward run: no evidence yet, status queued. */
export const queuedWalkForwardDetailResponse = {
  ...walkForwardDetailResponse,
  run: {
    ...walkForwardDetailResponse.run,
    run_id: 4,
    status: "queued",
    attempt_count: 0,
    claimed_at: null,
    heartbeat_at: null,
    lease_expires_at: null,
    started_at: "2026-12-02T00:00:00",
    finished_at: null
  },
  evidence: null,
  stitched_oos: null,
  windows: []
};

/** Running walk-forward run: status running with an active lease. */
export const runningWalkForwardDetailResponse = {
  ...queuedWalkForwardDetailResponse,
  run: {
    ...queuedWalkForwardDetailResponse.run,
    status: "running",
    attempt_count: 1,
    claimed_at: "2026-12-02T00:01:00",
    heartbeat_at: "2026-12-02T00:01:15",
    lease_expires_at: "2026-12-02T00:03:00"
  }
};

/** POST operation responses: writes land only in the in-memory simulator. */
export const operationResponses = {
  marketDataFetch: {
    status: "success",
    requested_etf_count: 3,
    rows_fetched: 30,
    rows_inserted: 28,
    rows_updated: 2,
    failed_symbols: [],
    error_message: null
  },
  bootstrap: {
    status: "success",
    steps: [
      { name: "migrate", status: "success", error_message: null },
      { name: "sync_etf_pool", status: "success", error_message: null },
      { name: "fetch_full_market_data", status: "success", error_message: null }
    ],
    total_duration_seconds: 12.4
  },
  generateSignal: {
    signal_id: 43,
    signal_date: "2026-06-24",
    config_version: "v1",
    status: "success",
    result: "rebalance",
    generated_at: "2026-06-24T09:30:00",
    is_fallback: false,
    source: "manual",
    positions: dashboardResponse.latest_signal.positions
  },
  runBacktest: {
    run_id: 8,
    status: "success",
    start_date: "2026-01-01",
    end_date: "2026-03-01",
    trading_day_count: 40,
    signal_count: 12,
    total_return: "0.087210",
    annualized_return: "0.603211",
    max_drawdown: "-0.043210",
    volatility: "0.098765",
    sharpe_ratio: "0.912345"
  },
  runWalkForward: {
    walk_forward_run_id: 9,
    status: "queued" as const
  }
};

export function operationFixtures(): ApiFixtureSpec[] {
  return [
    {
      method: "POST",
      path: "/api/market-data/fetch",
      query: { mode: "incremental" },
      body: operationResponses.marketDataFetch
    },
    {
      method: "POST",
      path: "/api/market-data/fetch",
      query: { mode: "full" },
      body: operationResponses.marketDataFetch
    },
    { method: "POST", path: "/api/setup/bootstrap", body: operationResponses.bootstrap },
    { method: "POST", path: "/api/strategy-signals/generate", body: operationResponses.generateSignal },
    {
      method: "POST",
      path: "/api/backtests/run",
      query: { startDate: "2026-01-01", endDate: "2026-03-01" },
      body: operationResponses.runBacktest
    },
    { method: "POST", path: "/api/walk-forwards/run", body: operationResponses.runWalkForward }
  ];
}
