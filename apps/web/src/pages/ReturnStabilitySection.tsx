import { useMemo, useState } from "react";
import {
  type ReturnStability,
  type ReturnStabilityCalendarBucket,
  type ReturnStabilityEntity,
  type ReturnStabilityRollingPoint
} from "../api/client";
import { EmptyState } from "../components";
import { formatDate } from "../utils/formatters";
import {
  computeMultiEquityCurveGeometry,
  EQUITY_CURVE_CHART,
  type EquityCurveChartPoint,
  type EquityCurveChartSeries
} from "./equityCurveChart";

export type RollingMetric = "return" | "volatility" | "sharpe";

const ROLLING_METRIC_OPTIONS: { value: RollingMetric; label: string }[] = [
  { value: "return", label: "Rolling Return" },
  { value: "volatility", label: "Rolling Volatility" },
  { value: "sharpe", label: "Rolling Sharpe" }
];

function metricValue(point: ReturnStabilityRollingPoint, metric: RollingMetric): number | null {
  const raw = point[metric === "return" ? "total_return" : metric === "volatility" ? "volatility" : "sharpe_ratio"];
  if (raw === null) {
    return null;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function metricAccessibleLabel(metric: RollingMetric): string {
  return ROLLING_METRIC_OPTIONS.find((option) => option.value === metric)?.label ?? metric;
}

function formatMetricValue(raw: string | null): string {
  return raw ?? "n/a";
}

export function ReturnStabilitySection({ stability }: { stability: ReturnStability }) {
  const [rollingMetric, setRollingMetric] = useState<RollingMetric>("return");
  const [calendarEntity, setCalendarEntity] = useState("strategy");

  const entities: { key: string; name: string; data: ReturnStabilityEntity }[] = [
    { key: "strategy", name: "Strategy", data: stability.strategy },
    ...stability.benchmarks.map((benchmark) => ({
      key: benchmark.key,
      name: benchmark.name,
      data: benchmark
    }))
  ];

  const selectedCalendar = entities.find((entity) => entity.key === calendarEntity) ?? entities[0];
  const insufficient = stability.strategy.rolling_status === "insufficient_observations";

  return (
    <section className="holdings-section" aria-labelledby="return-stability-heading">
      <h3 id="return-stability-heading">Return stability</h3>
      <p className="detail-note">
        63-session trailing window derived from persisted net values. Rolling and calendar
        values are computed by the backend; the browser displays API-provided results only.
      </p>
      {insufficient ? (
        <EmptyState>
          Fewer than 64 persisted points are available, so no 63-session rolling window can
          be formed. Calendar-period returns below remain available.
        </EmptyState>
      ) : null}

      {!insufficient ? (
        <RollingPanel
          entities={entities}
          metric={rollingMetric}
          onMetricChange={setRollingMetric}
        />
      ) : null}

      <CalendarPanel
        entities={entities}
        selectedKey={selectedCalendar.key}
        onEntityChange={setCalendarEntity}
      />
    </section>
  );
}

function RollingPanel({
  entities,
  metric,
  onMetricChange
}: {
  entities: { key: string; name: string; data: ReturnStabilityEntity }[];
  metric: RollingMetric;
  onMetricChange: (metric: RollingMetric) => void;
}) {
  const rollingEntities = entities.filter((entity) => entity.data.rolling.length > 0);

  if (rollingEntities.length === 0) {
    return (
      <div className="stability-subsection">
        <h4>Rolling metrics</h4>
        <EmptyState>No rolling windows are available.</EmptyState>
      </div>
    );
  }

  const sharpeUnavailable = rollingEntities.some(
    (entity) => entity.data.sharpe_status === "unavailable_missing_risk_free_rate"
  );

  return (
    <div className="stability-subsection">
      <div className="stability-controls">
        <h4>Rolling metrics</h4>
        <div aria-label="Rolling metric selector" className="stability-selector" role="group">
          {ROLLING_METRIC_OPTIONS.map((option) => (
            <button
              aria-pressed={metric === option.value}
              className="stability-selector-button"
              key={option.value}
              onClick={() => onMetricChange(option.value)}
              type="button"
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
      {sharpeUnavailable ? (
        <p className="detail-note">
          Sharpe is unavailable for this run because its historical parameters lack a
          risk-free rate; rolling return and volatility remain available.
        </p>
      ) : null}
      <RollingChart entities={entities} metric={metric} />
      <RollingTable entities={entities} metric={metric} />
    </div>
  );
}

function toChartSeries(
  entities: { key: string; name: string; data: ReturnStabilityEntity }[],
  metric: RollingMetric
): EquityCurveChartSeries[] {
  return entities.flatMap((entity) => {
    const points: EquityCurveChartPoint[] = entity.data.rolling.flatMap((point) => {
      const value = metricValue(point, metric);
      return value === null ? [] : [{ tradeDate: point.trade_date, netValue: value }];
    });
    return points.length > 0
      ? [{ key: entity.key, name: entity.name, points }]
      : [];
  });
}

function RollingChart({
  entities,
  metric
}: {
  entities: { key: string; name: string; data: ReturnStabilityEntity }[];
  metric: RollingMetric;
}) {
  const chartSeries = toChartSeries(entities, metric);
  const geometry = useMemo(
    () => computeMultiEquityCurveGeometry(chartSeries),
    [chartSeries]
  );

  if (geometry.series.length === 0) {
    return <EmptyState>No {metricAccessibleLabel(metric)} values are available to chart.</EmptyState>;
  }

  const anyMultiPoint = geometry.series.some((series) => series.points.length > 1);

  if (!anyMultiPoint) {
    const single = geometry.series[0];
    return (
      <div className="equity-curve-single-point">
        <EmptyState>Only one rolling point is available for {metricAccessibleLabel(metric)}.</EmptyState>
        <dl className="equity-curve-summary">
          {single.points.map((point) => (
            <DescriptionItem
              key={point.tradeDate}
              label={`${single.name} ${formatDate(point.tradeDate)}`}
              value={point.netValue.toFixed(6)}
            />
          ))}
        </dl>
      </div>
    );
  }

  const lastPoint = geometry.series[0].points[geometry.series[0].points.length - 1];
  return (
    <div className="equity-curve-card">
      <svg
        aria-labelledby={`rolling-chart-${metric}`}
        className="equity-curve-chart"
        role="img"
        viewBox={`0 0 ${EQUITY_CURVE_CHART.width} ${EQUITY_CURVE_CHART.height}`}
      >
        <title id={`rolling-chart-${metric}`}>
          {metricAccessibleLabel(metric)} comparison chart
        </title>
        <line
          className="equity-curve-grid-line"
          x1={EQUITY_CURVE_CHART.paddingLeft}
          x2={EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight}
          y1={EQUITY_CURVE_CHART.paddingTop}
          y2={EQUITY_CURVE_CHART.paddingTop}
        />
        <line
          className="equity-curve-grid-line"
          x1={EQUITY_CURVE_CHART.paddingLeft}
          x2={EQUITY_CURVE_CHART.width - EQUITY_CURVE_CHART.paddingRight}
          y1={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom}
          y2={EQUITY_CURVE_CHART.height - EQUITY_CURVE_CHART.paddingBottom}
        />
        {geometry.series.map((series, index) => (
          <path
            className="equity-curve-line"
            d={series.linePath}
            data-testid={`rolling-line-${metric}-${series.key}`}
            key={series.key}
            stroke={
              index === 0
                ? "var(--color-acid-lime)"
                : index === 1
                  ? "var(--color-signal-teal)"
                  : "var(--color-iris-violet)"
            }
          />
        ))}
      </svg>
      <ul aria-label={`${metricAccessibleLabel(metric)} legend`} className="equity-curve-legend">
        {geometry.series.map((series) => (
          <li key={series.key}>{series.name}</li>
        ))}
      </ul>
      <dl className="equity-curve-summary">
        <DescriptionItem label="Last window end" value={formatDate(lastPoint.tradeDate)} />
        <DescriptionItem label="Last value" value={lastPoint.netValue.toFixed(6)} />
      </dl>
    </div>
  );
}

function RollingTable({
  entities,
  metric
}: {
  entities: { key: string; name: string; data: ReturnStabilityEntity }[];
  metric: RollingMetric;
}) {
  return (
    <div className="holdings-table-wrap stability-table-wrap">
      <table className="holdings-table">
        <caption className="sr-only">Exact {metricAccessibleLabel(metric)} values by window</caption>
        <thead>
          <tr>
            <th scope="col">Entity</th>
            <th scope="col">Window start</th>
            <th scope="col">Trade date</th>
            <th scope="col">{metricAccessibleLabel(metric)}</th>
          </tr>
        </thead>
        <tbody>
          {entities.flatMap((entity) =>
            entity.data.rolling.map((point) => (
              <tr key={`${entity.key}-${point.trade_date}`}>
                <td>{entity.name}</td>
                <td>{formatDate(point.window_start_date)}</td>
                <td>{formatDate(point.trade_date)}</td>
                <td>{formatMetricValue(metricValueString(point, metric))}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function metricValueString(
  point: ReturnStabilityRollingPoint,
  metric: RollingMetric
): string | null {
  return point[metric === "return" ? "total_return" : metric === "volatility" ? "volatility" : "sharpe_ratio"];
}

function CalendarPanel({
  entities,
  selectedKey,
  onEntityChange
}: {
  entities: { key: string; name: string; data: ReturnStabilityEntity }[];
  selectedKey: string;
  onEntityChange: (key: string) => void;
}) {
  const selected = entities.find((entity) => entity.key === selectedKey) ?? entities[0];
  const hasAny = entities.some(
    (entity) => entity.data.monthly.length > 0 || entity.data.yearly.length > 0
  );

  if (!hasAny) {
    return (
      <div className="stability-subsection">
        <h4>Monthly and yearly returns</h4>
        <EmptyState>No calendar-period returns are available.</EmptyState>
      </div>
    );
  }

  return (
    <div className="stability-subsection">
      <div className="stability-controls">
        <h4>Monthly and yearly returns</h4>
        <label className="stability-select" htmlFor="stability-entity-select">
          Entity
          <select
            id="stability-entity-select"
            onChange={(event) => onEntityChange(event.target.value)}
            value={selected.key}
          >
            {entities.map((entity) => (
              <option key={entity.key} value={entity.key}>
                {entity.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <CalendarTable
        buckets={selected.data.monthly}
        entityName={selected.name}
        granularity="monthly"
      />
      <CalendarTable
        buckets={selected.data.yearly}
        entityName={selected.name}
        granularity="yearly"
      />
    </div>
  );
}

function CalendarTable({
  buckets,
  entityName,
  granularity
}: {
  buckets: ReturnStabilityCalendarBucket[];
  entityName: string;
  granularity: "monthly" | "yearly";
}) {
  if (buckets.length === 0) {
    return <EmptyState>No {granularity} returns are available for {entityName}.</EmptyState>;
  }

  return (
    <div className="holdings-table-wrap stability-table-wrap">
      <table className="holdings-table">
        <caption className="sr-only">{entityName} {granularity} returns</caption>
        <thead>
          <tr>
            <th scope="col">Period</th>
            <th scope="col">First date</th>
            <th scope="col">Last date</th>
            <th scope="col">Observations</th>
            <th scope="col">Total return</th>
            <th scope="col">Scope</th>
          </tr>
        </thead>
        <tbody>
          {buckets.map((bucket) => (
            <tr key={`${granularity}-${bucket.period}`}>
              <td>{bucket.period}</td>
              <td>{formatDate(bucket.first_date)}</td>
              <td>{formatDate(bucket.last_date)}</td>
              <td>{bucket.observation_count}</td>
              <td className={returnCellClass(bucket.total_return)}>
                {formatMetricValue(bucket.total_return)}
              </td>
              <td>{bucket.is_partial ? "partial" : "complete"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="detail-note">
        “Partial” marks periods the requested run bounds do not fully cover; it does not
        certify that every official session is present in the persisted curve.
      </p>
    </div>
  );
}

function returnCellClass(totalReturn: string): string {
  const value = Number(totalReturn);
  if (!Number.isFinite(value)) {
    return "stability-return-neutral";
  }
  if (value > 0) {
    return "stability-return-positive";
  }
  if (value < 0) {
    return "stability-return-negative";
  }
  return "stability-return-neutral";
}

function DescriptionItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
