import type { WalkForwardDetailResponse } from "../api/client";
import { DescriptionItem, EmptyState } from "../components";
import { formatDate } from "../utils/formatters";
import { computeEquityCurveGeometry, EQUITY_CURVE_CHART, normalizeEquityCurvePoints } from "./equityCurveChart";

export function StitchedOosSection({ data }: { data: WalkForwardDetailResponse }) {
  const stitched = data.stitched_oos;
  if (stitched === null) {
    return null;
  }
  if (stitched.status === "unavailable_non_contiguous_windows") {
    return <section className="holdings-section" aria-labelledby="stitched-oos-heading"><h2 id="stitched-oos-heading">Stitched OOS capital path</h2><p className="detail-note">Gap or overlap windows cannot form one chronological capital path. Independent OOS evidence remains available below.</p></section>;
  }
  const chartPoints = normalizeEquityCurvePoints(stitched.points);
  const geometry = chartPoints.length > 1 ? computeEquityCurveGeometry(chartPoints) : null;
  const resets = stitched.points.filter((point) => point.is_window_start);
  return <section className="holdings-section" aria-labelledby="stitched-oos-heading">
    <h2 id="stitched-oos-heading">Stitched OOS capital path</h2>
    <p className="detail-note">Compounds separately initialized OOS segments. No seam return, holdings carry, turnover, or transaction cost is synthesized.</p>
    <dl className="compact-list"><DescriptionItem label="Ending net value" mono value={stitched.ending_net_value ?? "n/a"} /><DescriptionItem label="Cumulative total return" mono value={stitched.total_return ?? "n/a"} /></dl>
    {geometry ? <svg aria-label="Stitched OOS equity curve" className="equity-curve-chart" role="img" viewBox={`0 0 ${EQUITY_CURVE_CHART.width} ${EQUITY_CURVE_CHART.height}`}><path className="equity-curve-line" d={geometry.linePath} fill="none" stroke="var(--chart-primary-line)" /></svg> : <EmptyState>No valid stitched OOS curve points are available for this run.</EmptyState>}
    <ul aria-label="Stitched OOS window resets">{resets.map((point) => <li key={`${point.window_ordinal}-${point.trade_date}`}>Window {point.window_ordinal + 1} reset: {formatDate(point.trade_date)}</li>)}</ul>
  </section>;
}
