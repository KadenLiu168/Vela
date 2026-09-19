import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { DashboardWalkForwardOos, DashboardWalkForwardSummary } from "../api/client";
import { OosRobustnessSection } from "./OosRobustnessSection";

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

function summary(overrides: Partial<DashboardWalkForwardSummary> = {}): DashboardWalkForwardSummary {
  return {
    run_id: 1,
    strategy_id: "Dual_momentum",
    status: "success",
    start_date: "2019-01-01",
    end_date: "2024-12-31",
    window_count: 5,
    finished_at: "2026-08-12T03:11:57",
    error_message: null,
    oos: oosEvidence,
    ...overrides
  };
}

function renderSection(walkForward: DashboardWalkForwardSummary | null) {
  return render(
    <MemoryRouter>
      <OosRobustnessSection walkForward={walkForward} />
    </MemoryRouter>
  );
}

describe("OosRobustnessSection", () => {
  it("states that no run exists yet and links to the walk-forward flow", () => {
    renderSection(null);

    expect(
      screen.getByText("No walk-forward run exists for the current strategy yet.")
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start a walk-forward run" })).toHaveAttribute(
      "href",
      "/walk-forwards"
    );
  });

  it("shows the run identity even when evidence is not available", () => {
    renderSection(summary({ status: "queued", window_count: 0, oos: null }));

    expect(screen.getByText("Walk-forward #1")).toBeInTheDocument();
    expect(screen.getByText("Queued")).toBeInTheDocument();
    expect(screen.getByText("2019-01-01 to 2024-12-31")).toBeInTheDocument();
  });

  it("renders persisted cross-window aggregates for a successful run", () => {
    renderSection(summary());

    expect(screen.getByText("4.10%")).toBeInTheDocument();
    expect(screen.getByText("0.62")).toBeInTheDocument();
    expect(screen.getByText("-11.80%")).toBeInTheDocument();
    expect(screen.getByText("60.00%")).toBeInTheDocument();
    expect(screen.getByText("50.00%")).toBeInTheDocument();
    expect(screen.getByText("vs CSI 300 buy-and-hold · 2/4 windows")).toBeInTheDocument();
  });

  it("explains the generalization gap and evidence sufficiency without scoring", () => {
    renderSection(summary());

    expect(
      screen.getByText(/Generalization gap \(IS Sharpe − OOS Sharpe\): median 0\.21/)
    ).toBeInTheDocument();
    expect(
      screen.getByText("Evidence status: sufficient — sufficient requires at least three valid windows.")
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "These are descriptive statistics across the independent per-window OOS estimates; they are not a combined capital path."
      )
    ).toBeInTheDocument();
    expect(screen.queryByText(/pass|fail|score/i)).not.toBeInTheDocument();
  });

  it("states why evidence is unavailable for a queued run", () => {
    renderSection(summary({ status: "queued", oos: null }));

    expect(
      screen.getByText("Evidence is unavailable until this queued run reaches a terminal state.")
    ).toBeInTheDocument();
    expect(screen.queryByText("4.10%")).not.toBeInTheDocument();
  });

  it("states why evidence is unavailable for a failed run and surfaces the error", () => {
    renderSection(
      summary({ status: "failed", oos: null, error_message: "missing market data" })
    );

    expect(
      screen.getByText("Evidence is unavailable because this run failed: missing market data")
    ).toBeInTheDocument();
  });

  it("links to the run's dedicated evidence page", () => {
    renderSection(summary());

    expect(screen.getByRole("link", { name: "View walk-forward evidence" })).toHaveAttribute(
      "href",
      "/walk-forwards/1"
    );
  });
});

describe("OosRobustnessSection loading state", () => {
  it("does not claim a run is absent while the dashboard is loading", () => {
    render(
      <MemoryRouter>
        <OosRobustnessSection isLoading walkForward={null} />
      </MemoryRouter>
    );

    expect(screen.getByText("Loading walk-forward evidence.")).toBeInTheDocument();
    expect(
      screen.queryByText("No walk-forward run exists for the current strategy yet.")
    ).not.toBeInTheDocument();
  });
});
