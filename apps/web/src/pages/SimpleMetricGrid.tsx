export function SimpleMetricGrid({
  items
}: {
  items: readonly (readonly [string, string])[];
}) {
  return items.map(([label, value]) => (
    <div className="metric-card" key={label}>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  ));
}
