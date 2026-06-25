type SignalDetailPageProps = {
  signalId: string;
};

export function SignalDetailPage({ signalId }: SignalDetailPageProps) {
  return (
    <section className="page detail-page">
      <div className="page-heading">
        <p>Signal research workspace</p>
        <h2>Signal Detail</h2>
      </div>
      <dl>
        <div>
          <dt>Signal ID</dt>
          <dd>Signal ID: {signalId}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>Placeholder for latest signal inputs and allocation review.</dd>
        </div>
      </dl>
    </section>
  );
}
