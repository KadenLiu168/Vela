import {
  computeSeriesEndLabels,
  EQUITY_CURVE_CHART,
  type EquityCurveChartCoordinate,
  type EquityCurveChartMultiGeometry
} from "./equityCurveChart";
import { seriesColor, seriesLineStyle } from "./seriesColor";

const {
  height,
  paddingBottom,
  paddingLeft,
  paddingRight,
  paddingTop,
  width
} = EQUITY_CURVE_CHART;
const chartRight = width - paddingRight;
const chartBottom = height - paddingBottom;

type EquityCurvePlotProps = {
  endLabelTestIdPrefix: string;
  geometry: EquityCurveChartMultiGeometry;
  highlightCoordinates?: EquityCurveChartCoordinate[];
  labelledBy: string;
  legendLabel: string;
  lineTestIdPrefix: string;
  singleLineTestId?: string;
  title: string;
  xTickTestId: string;
  yTickTestId: string;
  formatValueTick?: (value: number) => string;
};

export function EquityCurvePlot({
  endLabelTestIdPrefix,
  geometry,
  highlightCoordinates,
  labelledBy,
  legendLabel,
  lineTestIdPrefix,
  singleLineTestId,
  title,
  xTickTestId,
  yTickTestId,
  formatValueTick = (value) => value.toFixed(2)
}: EquityCurvePlotProps) {
  const endLabels = computeSeriesEndLabels(geometry.series);

  return (
    <>
      <svg
        aria-labelledby={labelledBy}
        className="equity-curve-chart"
        role="img"
        viewBox={`0 0 ${width} ${height}`}
      >
        <title id={labelledBy}>{title}</title>
        <path
          className="equity-curve-grid-line"
          d={`M ${paddingLeft} ${paddingTop} H ${chartRight} M ${paddingLeft} ${chartBottom} H ${chartRight}`}
        />
        <path
          aria-hidden="true"
          className="equity-curve-axis"
          d={`M ${paddingLeft} ${chartBottom} H ${chartRight} M ${paddingLeft} ${paddingTop} V ${chartBottom}`}
        />
        {geometry.dateTicks.map((tick) => (
          <text
            className="equity-curve-axis-tick"
            data-testid={xTickTestId}
            key={tick.value}
            textAnchor="middle"
            x={tick.x}
            y={chartBottom + 16}
          >
            {tick.value}
          </text>
        ))}
        {geometry.valueTicks.map((tick) => (
          <text
            className="equity-curve-axis-tick"
            data-testid={yTickTestId}
            key={tick.value}
            textAnchor="end"
            x={paddingLeft - 8}
            y={tick.y + 4}
          >
            {formatValueTick(tick.value)}
          </text>
        ))}
        {geometry.series.map((series) => (
          <path
            className="equity-curve-line"
            d={series.linePath}
            data-testid={
              geometry.series.length === 1 && singleLineTestId
                ? singleLineTestId
                : `${lineTestIdPrefix}${series.key}`
            }
            key={series.key}
            stroke={seriesColor(series.key)}
            strokeDasharray={seriesLineStyle(series.key)}
          />
        ))}
        {endLabels.map((label) => (
          <text
            className="equity-curve-end-label"
            data-testid={`${endLabelTestIdPrefix}${label.key}`}
            fill={seriesColor(label.key)}
            key={label.key}
            textAnchor="end"
            x={label.x}
            y={label.y}
          >
            {label.name}
          </text>
        ))}
        {highlightCoordinates?.map((coordinate) => (
          <circle
            className="equity-curve-highlight"
            cx={coordinate.x}
            cy={coordinate.y}
            data-testid="equity-curve-highlight"
            key={coordinate.index}
            r="4"
          />
        ))}
      </svg>
      <ul aria-label={legendLabel} className="equity-curve-legend">
        {geometry.series.map((series) => (
          <li className="equity-curve-legend-item" key={series.key}>
            {/* The swatch draws the same stroke and dash pattern as the
             * plotted line, so legend and chart share one line style. */}
            <svg
              aria-hidden="true"
              className="equity-curve-swatch"
              viewBox="0 0 16 10"
            >
              <line
                data-testid={`equity-curve-swatch-${series.key}`}
                stroke={seriesColor(series.key)}
                strokeDasharray={seriesLineStyle(series.key)}
                strokeWidth="2"
                x1="1"
                x2="15"
                y1="5"
                y2="5"
              />
            </svg>
            {series.name}
          </li>
        ))}
      </ul>
    </>
  );
}
