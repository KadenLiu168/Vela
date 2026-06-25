import { useEffect, useState } from "react";
import { ApiClientError, getHealth } from "../api/client";

export function DashboardPage() {
  const [apiStatus, setApiStatus] = useState("checking");

  useEffect(() => {
    let isCurrent = true;

    getHealth()
      .then((health) => {
        if (isCurrent) {
          setApiStatus(health.status);
        }
      })
      .catch((error: unknown) => {
        if (isCurrent) {
          setApiStatus(error instanceof ApiClientError ? error.kind : "unavailable");
        }
      });

    return () => {
      isCurrent = false;
    };
  }, []);

  return (
    <section className="page dashboard-page">
      <div className="page-heading">
        <p>Local research workflow</p>
        <h2>Workflow Dashboard</h2>
      </div>
      <div className="workflow-grid" aria-label="Research workflow status">
        <article>
          <span>Data</span>
          <strong>Market data ready for local checks</strong>
        </article>
        <article>
          <span>Signals</span>
          <strong>Latest signal workspace placeholder</strong>
        </article>
        <article>
          <span>Backtests</span>
          <strong>Recent backtest workspace placeholder</strong>
        </article>
      </div>
      <p className="api-status">API status: {apiStatus}</p>
    </section>
  );
}
