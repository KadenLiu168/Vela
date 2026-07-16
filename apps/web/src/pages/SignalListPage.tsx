import { useEffect, useState } from "react";
import {
  ApiClientError,
  type StrategySignalListItem,
  listStrategySignals
} from "../api/client";
import { EmptyState, FeedbackMessage, Pagination } from "../components";
import { formatDate, formatNullableText, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 20;

type SignalListState =
  | { status: "loading"; data?: never; error?: never; offset?: never }
  | { status: "ready"; data: StrategySignalListItem[]; error?: never; offset: number }
  | { status: "error"; data?: never; error: string; offset: number };

export function SignalListPage() {
  const [offset, setOffset] = useState(0);
  const [signalState, setSignalState] = useState<SignalListState>({
    status: "loading"
  });

  useEffect(() => {
    let isCurrent = true;

    listStrategySignals(PAGE_SIZE, offset)
      .then((data) => {
        if (isCurrent) {
          setSignalState({ status: "ready", data: data.signals, offset });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        setSignalState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable",
          offset
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [offset]);

  return (
    <section className="page list-page signal-list-page">
      <div className="page-heading">
        <p>Signal research workspace</p>
        <h1>Signals</h1>
      </div>
      {renderSignalList(getSignalListState(signalState, offset), offset, setOffset)}
    </section>
  );
}

function getSignalListState(state: SignalListState, offset: number): SignalListState {
  return state.status === "loading" || state.offset === offset ? state : { status: "loading" };
}

function renderSignalList(
  state: SignalListState,
  offset: number,
  setOffset: (value: number) => void
) {
  if (state.status === "loading") {
    return <FeedbackMessage variant="loading">Loading signal history.</FeedbackMessage>;
  }

  if (state.status === "error") {
    return (
      <FeedbackMessage className="dashboard-alert" variant="error">
        Signal history API unavailable: {state.error}
      </FeedbackMessage>
    );
  }

  if (state.data.length === 0 && offset === 0) {
    return (
      <EmptyState>
        No successful local signal exists yet. Generate a signal from the Dashboard after market data is ready.
      </EmptyState>
    );
  }

  return (
    <article className="dashboard-panel">
      <div className="holdings-table-wrap">
        <table className="holdings-table">
          <thead>
            <tr>
              <th scope="col">Signal</th>
              <th scope="col">Signal date</th>
              <th scope="col">Config version</th>
              <th scope="col">Result</th>
              <th scope="col">Generated at</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((signal) => (
              <tr key={signal.signal_id}>
                <td>
                  <a className="operation-link" href={`/signals/${signal.signal_id}`}>
                    #{signal.signal_id}
                  </a>
                </td>
                <td>{formatDate(signal.signal_date)}</td>
                <td>{signal.config_version}</td>
                <td>{formatNullableText(signal.result)}</td>
                <td>{formatTimestamp(signal.generated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        offset={offset}
        pageSize={PAGE_SIZE}
        itemCount={state.data.length}
        onOffsetChange={setOffset}
      />
    </article>
  );
}
