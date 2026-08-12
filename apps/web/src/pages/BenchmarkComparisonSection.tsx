import type { BacktestBenchmark, BacktestDetailMetrics } from "../api/client";
import {
  formatDate,
  formatDecimal,
  formatNullableInteger,
  formatRatioAsPercent
} from "../utils/formatters";
import { bestCellIndexes, type ComparisonRow } from "./comparisonMatrix";

type BenchmarkComparisonSectionProps = {
  metrics: BacktestDetailMetrics;
  benchmarks: BacktestBenchmark[];
};

function toComparableNumber(value: string | null): number | null {
  if (value === null) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/**
 * Side-by-side strategy versus benchmark comparison split into two groups: an
 * always-visible core metrics table and a closed-by-default Advanced Metrics
 * disclosure holding the remaining drawdown/relative evidence. Best-value
 * markers follow the documented direction rules on comparable absolute rows.
 */
export function BenchmarkComparisonSection({
  metrics,
  benchmarks
}: BenchmarkComparisonSectionProps) {
  if (benchmarks.length === 0) {
    return (
      <section
        aria-labelledby="benchmark-comparison-heading"
        className="holdings-section"
      >
        <h3 id="benchmark-comparison-heading">Benchmark comparison</h3>
        <p className="detail-note">No benchmark comparison is available for this run.</p>
      </section>
    );
  }

  const entities: BacktestDetailMetrics[] = [metrics, ...benchmarks];
  const toNumber = toComparableNumber;

  const coreRows: ComparisonRow[] = [
    {
      key: "total_return",
      label: "Total return",
      cells: entities.map((entity) => formatRatioAsPercent(entity.total_return)),
      numeric: entities.map((entity) => toNumber(entity.total_return)),
      direction: "higher",
      rankable: true
    },
    {
      key: "annualized_return",
      label: "CAGR (calendar-time)",
      cells: entities.map((entity) => formatRatioAsPercent(entity.annualized_return)),
      numeric: entities.map((entity) => toNumber(entity.annualized_return)),
      direction: "higher",
      rankable: true
    },
    {
      key: "max_drawdown",
      label: "Max drawdown",
      cells: entities.map((entity) => formatRatioAsPercent(entity.max_drawdown)),
      numeric: entities.map((entity) => toNumber(entity.max_drawdown)),
      direction: "closest-to-zero",
      rankable: true
    },
    {
      key: "volatility",
      label: "Annualized volatility (252D)",
      cells: entities.map((entity) => formatRatioAsPercent(entity.volatility)),
      numeric: entities.map((entity) => toNumber(entity.volatility)),
      direction: "lower",
      rankable: true
    },
    {
      key: "sharpe_ratio",
      label: "Sharpe (daily returns, 252D)",
      cells: entities.map((entity) => formatDecimal(entity.sharpe_ratio, 2, false)),
      numeric: entities.map((entity) => toNumber(entity.sharpe_ratio)),
      direction: "higher",
      rankable: true
    },
    {
      key: "sortino_ratio",
      label: "Sortino (rf MAR, 252D)",
      cells: entities.map((entity) => formatDecimal(entity.sortino_ratio, 6, false)),
      numeric: entities.map((entity) => toNumber(entity.sortino_ratio)),
      direction: "higher",
      rankable: true
    },
    {
      key: "calmar_ratio",
      label: "Calmar (calendar CAGR / |MaxDD|)",
      cells: entities.map((entity) => formatDecimal(entity.calmar_ratio, 6, false)),
      numeric: entities.map((entity) => toNumber(entity.calmar_ratio)),
      direction: "higher",
      rankable: true
    }
  ];

  const drawdownRows: ComparisonRow[] = [
    {
      key: "longest_drawdown_duration_sessions",
      label: "Longest drawdown duration (official sessions)",
      cells: entities.map((entity) =>
        formatNullableInteger(entity.longest_drawdown_duration_sessions)
      ),
      numeric: entities.map((entity) => entity.longest_drawdown_duration_sessions),
      direction: "lower",
      rankable: true
    },
    {
      key: "longest_drawdown_peak_date",
      label: "Longest drawdown peak date",
      cells: entities.map((entity) => formatDate(entity.longest_drawdown_peak_date))
    },
    {
      key: "longest_drawdown_trough_date",
      label: "Longest drawdown trough date",
      cells: entities.map((entity) => formatDate(entity.longest_drawdown_trough_date))
    },
    {
      key: "longest_drawdown_recovery",
      label: "Longest drawdown recovery",
      cells: entities.map((entity) => formatDrawdownRecovery(entity))
    }
  ];

  const relativeRows: ComparisonRow[] = [
    {
      key: "tracking_error",
      label: "Tracking error (252D)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatDecimal(benchmark.tracking_error, 6, false))]
    },
    {
      key: "information_ratio",
      label: "Information ratio (252D)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatDecimal(benchmark.information_ratio, 6, false))]
    },
    {
      key: "up_capture_ratio",
      label: "Monthly Up Capture (selected months)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.up_capture_ratio))]
    },
    {
      key: "up_count",
      label: "Up selected months",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatNullableInteger(benchmark.up_capture_observation_count))]
    },
    {
      key: "down_capture_ratio",
      label: "Monthly Down Capture (selected months)",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.down_capture_ratio))]
    },
    {
      key: "down_count",
      label: "Down selected months",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatNullableInteger(benchmark.down_capture_observation_count))]
    },
    {
      key: "total_return_difference",
      label: "Strategy total return difference",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.total_return_difference))]
    },
    {
      key: "annualized_return_difference",
      label: "Strategy CAGR difference",
      cells: ["n/a", ...benchmarks.map((benchmark) => formatRatioAsPercent(benchmark.annualized_return_difference))]
    }
  ];

  return (
    <section
      aria-labelledby="benchmark-comparison-heading"
      className="holdings-section"
    >
      <h3 id="benchmark-comparison-heading">Benchmark comparison</h3>
      <div
        aria-label="Strategy vs benchmark comparison matrix region"
        className="comparison-matrix-wrap"
        tabIndex={0}
      >
        <table className="comparison-matrix holdings-table">
          <caption className="sr-only">Strategy vs benchmark comparison matrix</caption>
          <thead>
            <tr>
              <th scope="col">Metric</th>
              <th scope="col">Strategy</th>
              {benchmarks.map((benchmark) => (
                <th scope="col" key={benchmark.key}>
                  {benchmark.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody aria-label="Absolute metrics">
            {coreRows.map((row) => (
              <MatrixRow key={row.key} row={row} />
            ))}
          </tbody>
        </table>
      </div>
      <details className="disclosure">
        <summary className="disclosure-summary">
          <h4 className="disclosure-heading" id="advanced-metrics-heading">
            Advanced metrics
          </h4>
        </summary>
        <div className="disclosure-body">
          <div
            aria-label="Advanced strategy vs benchmark comparison matrix region"
            className="comparison-matrix-wrap"
            tabIndex={0}
          >
            <table className="comparison-matrix holdings-table">
              <caption className="sr-only">
                Advanced strategy vs benchmark comparison metrics
              </caption>
              <thead>
                <tr>
                  <th scope="col">Metric</th>
                  <th scope="col">Strategy</th>
                  {benchmarks.map((benchmark) => (
                    <th scope="col" key={benchmark.key}>
                      {benchmark.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody aria-label="Drawdown evidence">
                {drawdownRows.map((row) => (
                  <MatrixRow key={row.key} row={row} />
                ))}
              </tbody>
              <tbody aria-label="Strategy-relative metrics">
                {relativeRows.map((row) => (
                  <MatrixRow key={row.key} row={row} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </details>
    </section>
  );
}

function MatrixRow({ row }: { row: ComparisonRow }) {
  const bestIndexes = new Set(bestCellIndexes(row));
  return (
    <tr data-testid={`comparison-row-${row.key}`}>
      <th scope="row">{row.label}</th>
      {row.cells.map((cell, index) => (
        <td className={bestIndexes.has(index) ? "comparison-best" : undefined} key={index}>
          {cell}
          {bestIndexes.has(index) ? <span className="comparison-best-badge">Best</span> : null}
        </td>
      ))}
    </tr>
  );
}

function formatDrawdownRecovery(
  metrics: Pick<
    BacktestDetailMetrics,
    | "longest_drawdown_duration_sessions"
    | "longest_drawdown_peak_date"
    | "longest_drawdown_trough_date"
    | "longest_drawdown_recovery_date"
  >
): string {
  if (metrics.longest_drawdown_recovery_date) {
    return formatDate(metrics.longest_drawdown_recovery_date);
  }

  return metrics.longest_drawdown_duration_sessions !== null &&
    metrics.longest_drawdown_duration_sessions > 0 &&
    metrics.longest_drawdown_peak_date !== null &&
    metrics.longest_drawdown_trough_date !== null
    ? "ongoing"
    : "n/a";
}
