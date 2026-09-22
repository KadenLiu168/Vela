import type { BacktestBenchmark, BacktestDetailMetrics } from "../api/client";
import {
  formatDate,
  formatDecimal,
  formatNullableInteger,
  formatRatioAsPercent
} from "../utils/formatters";
import { parseMetricNumber } from "./backtestFormatters";
import { bestCellIndexes, type ComparisonRow } from "./comparisonMatrix";
import { formatDrawdownRecovery } from "./drawdownFormatters";

type BenchmarkComparisonSectionProps = {
  metrics: BacktestDetailMetrics;
  benchmarks: BacktestBenchmark[];
};

type CoreMetricKey =
  | "total_return"
  | "annualized_return"
  | "max_drawdown"
  | "volatility"
  | "sharpe_ratio"
  | "sortino_ratio"
  | "calmar_ratio";

const CORE_METRICS: readonly [CoreMetricKey, string, "higher" | "lower" | "closest-to-zero"][] = [
  ["total_return", "Total return", "higher"],
  ["annualized_return", "CAGR (calendar-time)", "higher"],
  ["max_drawdown", "Max drawdown", "closest-to-zero"],
  ["volatility", "Annualized volatility (252D)", "lower"],
  ["sharpe_ratio", "Sharpe (daily returns, 252D)", "higher"],
  ["sortino_ratio", "Sortino (rf MAR, 252D)", "higher"],
  ["calmar_ratio", "Calmar (calendar CAGR / |MaxDD|)", "higher"]
];

type ComparisonValue = (entity: BacktestDetailMetrics) => string;
type ComparisonNumber = (entity: BacktestDetailMetrics) => number | null;

type ComparisonDefinition = {
  key: string;
  label: string;
  format: ComparisonValue;
  numeric?: ComparisonNumber;
  direction?: ComparisonRow["direction"];
};

function formatCoreMetric(key: CoreMetricKey, value: string | null): string {
  if (key === "sharpe_ratio") {
    return formatDecimal(value, 2, false);
  }
  if (key === "sortino_ratio" || key === "calmar_ratio") {
    return formatDecimal(value, 6, false);
  }
  return formatRatioAsPercent(value);
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
  const coreRows: ComparisonRow[] = CORE_METRICS.map(([key, label, direction]) => {
    const values = entities.map((entity) => entity[key]);
    return {
      key,
      label,
      cells: values.map((value) => formatCoreMetric(key, value)),
      numeric: values.map(parseMetricNumber),
      direction,
      rankable: true
    };
  });

  const drawdownRows = buildRows(entities, [
    {
      key: "longest_drawdown_duration_sessions",
      label: "Longest drawdown duration (official sessions)",
      format: (entity) => formatNullableInteger(entity.longest_drawdown_duration_sessions),
      numeric: (entity) => entity.longest_drawdown_duration_sessions,
      direction: "lower"
    },
    {
      key: "longest_drawdown_peak_date",
      label: "Longest drawdown peak date",
      format: (entity) => formatDate(entity.longest_drawdown_peak_date)
    },
    {
      key: "longest_drawdown_trough_date",
      label: "Longest drawdown trough date",
      format: (entity) => formatDate(entity.longest_drawdown_trough_date)
    },
    {
      key: "longest_drawdown_recovery",
      label: "Longest drawdown recovery",
      format: formatDrawdownRecovery
    }
  ]);

  const relativeRows = buildRelativeRows(benchmarks, [
    [
      "tracking_error",
      "Tracking error (252D)",
      (benchmark) => formatDecimal(benchmark.tracking_error, 6, false)
    ],
    [
      "information_ratio",
      "Information ratio (252D)",
      (benchmark) => formatDecimal(benchmark.information_ratio, 6, false)
    ],
    [
      "up_capture_ratio",
      "Monthly Up Capture (selected months)",
      (benchmark) => formatRatioAsPercent(benchmark.up_capture_ratio)
    ],
    [
      "up_count",
      "Up selected months",
      (benchmark) => formatNullableInteger(benchmark.up_capture_observation_count)
    ],
    [
      "down_capture_ratio",
      "Monthly Down Capture (selected months)",
      (benchmark) => formatRatioAsPercent(benchmark.down_capture_ratio)
    ],
    [
      "down_count",
      "Down selected months",
      (benchmark) => formatNullableInteger(benchmark.down_capture_observation_count)
    ],
    [
      "total_return_difference",
      "Strategy total return difference",
      (benchmark) => formatRatioAsPercent(benchmark.total_return_difference)
    ],
    [
      "annualized_return_difference",
      "Strategy CAGR difference",
      (benchmark) => formatRatioAsPercent(benchmark.annualized_return_difference)
    ]
  ]);

  return (
    <section
      aria-labelledby="benchmark-comparison-heading"
      className="holdings-section"
    >
      <h3 id="benchmark-comparison-heading">Benchmark comparison</h3>
      <ComparisonTable
        benchmarks={benchmarks}
        caption="Strategy vs benchmark comparison matrix"
        groups={[{ label: "Absolute metrics", rows: coreRows }]}
        regionLabel="Strategy vs benchmark comparison matrix region"
      />
      <details className="disclosure">
        <summary className="disclosure-summary">
          <h4 className="disclosure-heading" id="advanced-metrics-heading">
            Advanced metrics
          </h4>
        </summary>
        <div className="disclosure-body">
          <ComparisonTable
            benchmarks={benchmarks}
            caption="Advanced strategy vs benchmark comparison metrics"
            groups={[
              { label: "Drawdown evidence", rows: drawdownRows },
              { label: "Strategy-relative metrics", rows: relativeRows }
            ]}
            regionLabel="Advanced strategy vs benchmark comparison matrix region"
          />
        </div>
      </details>
    </section>
  );
}

function buildRows(
  entities: BacktestDetailMetrics[],
  definitions: ComparisonDefinition[]
): ComparisonRow[] {
  return definitions.map(({ key, label, format, numeric, direction }) => {
    const row: ComparisonRow = { key, label, cells: entities.map(format) };
    if (numeric && direction) {
      row.numeric = entities.map(numeric);
      row.direction = direction;
      row.rankable = true;
    }
    return row;
  });
}

type RelativeValue = (benchmark: BacktestBenchmark) => string;

function buildRelativeRows(
  benchmarks: BacktestBenchmark[],
  definitions: [string, string, RelativeValue][]
): ComparisonRow[] {
  return definitions.map(([key, label, format]) => ({
    key,
    label,
    cells: ["n/a", ...benchmarks.map(format)]
  }));
}

function ComparisonTable({
  benchmarks,
  caption,
  groups,
  regionLabel
}: {
  benchmarks: BacktestBenchmark[];
  caption: string;
  groups: { label: string; rows: ComparisonRow[] }[];
  regionLabel: string;
}) {
  return (
    <div aria-label={regionLabel} className="comparison-matrix-wrap" tabIndex={0}>
      <table className="comparison-matrix holdings-table">
        <caption className="sr-only">{caption}</caption>
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
        {groups.map((group) => (
          <tbody aria-label={group.label} key={group.label}>
            {group.rows.map((row) => (
              <MatrixRow key={row.key} row={row} />
            ))}
          </tbody>
        ))}
      </table>
    </div>
  );
}

function MatrixRow({ row }: { row: ComparisonRow }) {
  const bestIndexes = new Set(bestCellIndexes(row));
  return (
    <tr data-testid={`comparison-row-${row.key}`}>
      <th scope="row">{row.label}</th>
      {row.cells.map((cell, index) => (
        <td className={bestIndexes.has(index) ? "mono-compact comparison-best" : "mono-compact"} key={index}>
          {cell}
          {bestIndexes.has(index) ? <span className="comparison-best-badge">Best</span> : null}
        </td>
      ))}
    </tr>
  );
}
