import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import type { BacktestDetailRun } from "../api/client";
import { ExperimentConfigSection } from "./ExperimentConfigSection";

const run = (parametersJson: string | null): BacktestDetailRun => ({
  run_id: 7,
  strategy_id: "s",
  config_version: "v1",
  start_date: "2026-01-01",
  end_date: "2026-01-02",
  parameters_json: parametersJson,
  status: "success",
  error_message: null,
  started_at: "2026-01-01T00:00:00",
  finished_at: "2026-01-01T00:01:00"
});

const parametersPayload = JSON.stringify({
  strategy_id: "s",
  config_version: "v1",
  type: "dual_momentum",
  start_date: "2026-01-01",
  end_date: "2026-01-02",
  risk_free_rate: 0.02,
  performance_metric_version: "perf_v3",
  equity_model_version: "eq_v2",
  tail_distribution_metric_version: "tail_v1",
  benchmark_regime_metric_version: "regime_v1",
  custom_flag: "raw-value"
});

/** The human-readable parameters list (distinct from the run metadata list). */
function parameterList() {
  return within(screen.getByText("Annualized risk-free rate").closest("dl") as HTMLElement);
}

/** The full run metadata list. */
function metadataList() {
  return within(screen.getByText("Started at").closest("dl") as HTMLElement);
}

function rawParametersDetails() {
  return screen.getByRole("heading", { name: "Raw parameters" }).closest("details") as HTMLElement;
}

it("renders the full run metadata and human-readable known parameters", () => {
  render(<ExperimentConfigSection run={run(parametersPayload)} />);

  const metadata = metadataList();
  expect(metadata.getByText("Strategy")).toBeInTheDocument();
  expect(metadata.getByText("s")).toBeInTheDocument();
  expect(metadata.getByText("Config version")).toBeInTheDocument();
  expect(metadata.getByText("v1")).toBeInTheDocument();
  expect(metadata.getByText("2026-01-01 to 2026-01-02")).toBeInTheDocument();
  expect(metadata.getByText("success")).toBeInTheDocument();
  expect(metadata.getByText("2026-01-01T00:00:00")).toBeInTheDocument();
  expect(metadata.getByText("2026-01-01T00:01:00")).toBeInTheDocument();

  const params = parameterList();
  expect(params.getByText("Strategy")).toBeInTheDocument();
  expect(params.getByText("Config version")).toBeInTheDocument();
  expect(params.getByText("Strategy type")).toBeInTheDocument();
  expect(params.getByText("Dual momentum")).toBeInTheDocument();
  expect(params.getByText("Start date")).toBeInTheDocument();
  expect(params.getByText("End date")).toBeInTheDocument();
  expect(params.getByText("Annualized risk-free rate")).toBeInTheDocument();
  expect(params.getByText("Performance metric version")).toBeInTheDocument();
  expect(params.getByText("perf_v3")).toBeInTheDocument();
  expect(params.getByText("Equity model version")).toBeInTheDocument();
  expect(params.getByText("eq_v2")).toBeInTheDocument();
  expect(params.getByText("Tail distribution metric version")).toBeInTheDocument();
  expect(params.getByText("tail_v1")).toBeInTheDocument();
  expect(params.getByText("Benchmark regime metric version")).toBeInTheDocument();
  expect(params.getByText("regime_v1")).toBeInTheDocument();
});

it("renders the annualized risk-free rate as a percentage rather than a decimal", () => {
  render(<ExperimentConfigSection run={run(parametersPayload)} />);

  const params = parameterList();
  expect(params.getByText("2.0%")).toBeInTheDocument();
  expect(params.queryByText("0.02")).not.toBeInTheDocument();
});

it("falls back to raw key and value text for unknown keys", () => {
  render(<ExperimentConfigSection run={run(parametersPayload)} />);

  const params = parameterList();
  expect(params.getByText("custom_flag")).toBeInTheDocument();
  expect(params.getByText("raw-value")).toBeInTheDocument();
});

it("keeps Raw Parameters as a closed-by-default disclosure with the original JSON", () => {
  render(<ExperimentConfigSection run={run(parametersPayload)} />);

  const details = rawParametersDetails();
  expect(details).not.toHaveAttribute("open");
  const pre = within(details).getByText(/"risk_free_rate": 0\.02/);
  expect(pre.tagName).toBe("PRE");
  expect(within(details).getByText(/"type": "dual_momentum"/)).toBeInTheDocument();
});

it("renders no parameter list and an n/a raw disclosure for null parameters", () => {
  render(<ExperimentConfigSection run={run(null)} />);

  expect(screen.queryByText("Annualized risk-free rate")).not.toBeInTheDocument();
  const details = rawParametersDetails();
  expect(within(details).getByText("n/a")).toBeInTheDocument();
});
