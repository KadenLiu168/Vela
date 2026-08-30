import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import type { EquityCurveChartMultiGeometry } from "./equityCurveChart";
import { EquityCurvePlot } from "./EquityCurvePlot";

const geometry: EquityCurveChartMultiGeometry = {
  dateTicks: [{ value: "2026-01-01", x: 48 }],
  maxNetValue: 1,
  minNetValue: 1,
  series: [{
    endpoints: {
      first: { index: 0, x: 48, y: 100 },
      last: { index: 0, x: 48, y: 100 }
    },
    key: "strategy",
    linePath: "M 48.00 100.00",
    name: "Strategy",
    points: []
  }],
  valueTicks: [{ value: 1, y: 100 }]
};

it("renders the shared chart frame with caller-specific identifiers", () => {
  render(
    <EquityCurvePlot
      endLabelTestIdPrefix="end-"
      geometry={geometry}
      labelledBy="chart-title"
      legendLabel="Test legend"
      lineTestIdPrefix="line-"
      title="Test chart"
      xTickTestId="x-tick"
      yTickTestId="y-tick"
    />
  );

  expect(screen.getByRole("img", { name: "Test chart" })).toBeInTheDocument();
  expect(screen.getByTestId("x-tick")).toHaveTextContent("2026-01-01");
  expect(screen.getByTestId("y-tick")).toHaveTextContent("1.00");
  expect(screen.getByTestId("line-strategy")).toBeInTheDocument();
  expect(screen.getByTestId("end-strategy")).toBeInTheDocument();
  expect(screen.getByRole("list", { name: "Test legend" })).toHaveTextContent("Strategy");
});
