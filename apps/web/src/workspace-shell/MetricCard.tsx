export function MetricCard({ metric, value }: { metric: string; value: string | number }) {
  return (
    <article className="metric-card">
      <p>{metric}</p>
      <strong>{value}</strong>
    </article>
  );
}
