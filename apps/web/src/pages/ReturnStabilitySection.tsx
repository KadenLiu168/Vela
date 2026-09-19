import { useMemo, useState, type ReactNode } from "react";
import {
  type ReturnStability,
  type ReturnStabilityCalendarBucket,
  type ReturnStabilityEntity,
  type ReturnStabilityRollingPoint
} from "../api/client";
import { EmptyState } from "../components";
import { formatDate, formatNullableText } from "../utils/formatters";
import {
  computeMultiEquityCurveGeometry,
  type EquityCurveChartPoint,
  type EquityCurveChartSeries
} from "./equityCurveChart";
import { EquityCurvePlot } from "./EquityCurvePlot";
import { SimpleMetricGrid } from "./SimpleMetricGrid";
import { TableCells, TableHeader } from "./tablePrimitives";

export type RollingMetric = "return" | "volatility" | "sharpe";

const ROLLING_METRIC_OPTIONS: { value: RollingMetric; label: string }[] = [
  { value: "return", label: "Rolling Return" },
  { value: "volatility", label: "Rolling Volatility" },
  { value: "sharpe", label: "Rolling Sharpe" }
];

const ROLLING_TABLE_COLUMNS = ["Entity", "Window start", "Trade date"];
const CALENDAR_TABLE_COLUMNS = [
  "Period",
  "First date",
  "Last date",
  "Observations",
  "Total return",
  "Scope"
];

function metricValue(point: ReturnStabilityRollingPoint, metric: RollingMetric): number | null {
  const raw = metricValueString(point, metric);
  if (raw === null) {
    return null;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function metricAccessibleLabel(metric: RollingMetric): string {
  return ROLLING_METRIC_OPTIONS.find((option) => option.value === metric)?.label ?? metric;
}

/** Y-axis tick labels use the selected metric's own scale: Return and
 *  Volatility are ratios rendered as percentages; Sharpe is a ratio. */
function formatRollingTick(metric: RollingMetric, value: number): string {
  if (metric === "sharpe") {
    return value.toFixed(1);
  }
  return `${(value * 100).toFixed(0)}%`;
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
    <details className="disclosure">
      <summary className="disclosure-summary">
        <h3 className="disclosure-heading" id="return-stability-heading">
          Return stability
        </h3>
      </summary>
      <div className="disclosure-body">
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
      </div>
    </details>
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
              className="button-secondary"
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
          <SimpleMetricGrid
            items={single.points.map((point) => [
              `${single.name} ${formatDate(point.tradeDate)}`,
              point.netValue.toFixed(6)
            ])}
          />
        </dl>
      </div>
    );
  }

  const lastPoint = geometry.series[0].points[geometry.series[0].points.length - 1];
  return (
    <div className="equity-curve-card">
      <EquityCurvePlot
        endLabelTestIdPrefix={`rolling-end-label-${metric}-`}
        formatValueTick={(value) => formatRollingTick(metric, value)}
        geometry={geometry}
        labelledBy={`rolling-chart-${metric}`}
        legendLabel={`${metricAccessibleLabel(metric)} legend`}
        lineTestIdPrefix={`rolling-line-${metric}-`}
        title={`${metricAccessibleLabel(metric)} comparison chart`}
        xTickTestId="rolling-x-tick"
        yTickTestId="rolling-y-tick"
      />
      <dl className="equity-curve-summary">
        <SimpleMetricGrid
          items={[
            ["Last window end", formatDate(lastPoint.tradeDate)],
            ["Last value", lastPoint.netValue.toFixed(6)]
          ]}
        />
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
    <StabilityTable
      columns={[...ROLLING_TABLE_COLUMNS, metricAccessibleLabel(metric)]}
      caption={`Exact ${metricAccessibleLabel(metric)} values by window`}
    >
      {entities.flatMap((entity) =>
        entity.data.rolling.map((point) => (
          <tr key={`${entity.key}-${point.trade_date}`}>
            <TableCells
              cells={[
                entity.name,
                formatDate(point.window_start_date),
                formatDate(point.trade_date),
                metricValueString(point, metric) ?? "n/a"
              ]}
            />
          </tr>
        ))
      )}
    </StabilityTable>
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
    <>
      <StabilityTable columns={CALENDAR_TABLE_COLUMNS} caption={`${entityName} ${granularity} returns`}>
        {buckets.map((bucket) => (
          <tr key={`${granularity}-${bucket.period}`}>
            <TableCells
              cells={[
                bucket.period,
                formatDate(bucket.first_date),
                formatDate(bucket.last_date),
                bucket.observation_count
              ]}
            />
            <td className={returnCellClass(bucket.total_return)}>
              {formatNullableText(bucket.total_return)}
            </td>
            <TableCells cells={[bucket.is_partial ? "partial" : "complete"]} />
          </tr>
        ))}
      </StabilityTable>
      <p className="detail-note">
        “Partial” marks periods the requested run bounds do not fully cover; it does not
        certify that every official session is present in the persisted curve.
      </p>
    </>
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

function StabilityTable({
  caption,
  columns,
  children
}: {
  caption: string;
  columns: string[];
  children: ReactNode;
}) {
  return (
    <div className="holdings-table-wrap stability-table-wrap">
      <table className="holdings-table">
        <caption className="sr-only">{caption}</caption>
        <TableHeader columns={columns} />
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
