type BacktestDetailPageProps = {
  backtestId: string;
};

export function BacktestDetailPage({ backtestId }: BacktestDetailPageProps) {
  return (
    <section className="page detail-page">
      <div className="page-heading">
        <p>Backtest research workspace</p>
        <h2>Backtest Detail</h2>
      </div>
      <dl>
        <div>
          <dt>Backtest ID</dt>
          <dd>Backtest ID: {backtestId}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>Placeholder for equity curve, risk metrics, and run notes.</dd>
        </div>
      </dl>
    </section>
  );
}
