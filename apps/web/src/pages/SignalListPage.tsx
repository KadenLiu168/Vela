import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  ApiClientError,
  type StrategySignalListItem,
  type StrategySignalSource,
  listStrategySignals
} from "../api/client";
import { EmptyState, FeedbackMessage, Pagination } from "../components";
import { formatDate, formatNullableText, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 20;

type SignalListState =
  | { status: "loading"; data?: never; error?: never; offset?: never }
  | {
      status: "ready";
      data: StrategySignalListItem[];
      error?: never;
      offset: number;
      source: StrategySignalSource | undefined;
    }
  | {
      status: "error";
      data?: never;
      error: string;
      offset: number;
      source: StrategySignalSource | undefined;
    };

export function SignalListPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const rawSource = searchParams.get("source");
  const source = isStrategySignalSource(rawSource) ? rawSource : undefined;
  const [offset, setOffset] = useState(0);
  const [signalState, setSignalState] = useState<SignalListState>({
    status: "loading"
  });

  // Normalize an invalid source value through Router replacement navigation,
  // preserving unrelated query parameters and the hash.
  useEffect(() => {
    if (rawSource !== null && !isStrategySignalSource(rawSource)) {
      const params = new URLSearchParams(location.search);
      params.delete("source");
      const search = params.toString();
      navigate(`${location.pathname}${search ? `?${search}` : ""}${location.hash}`, {
        replace: true
      });
    }
  }, [rawSource, location, navigate]);

  useEffect(() => {
    let isCurrent = true;

    listStrategySignals(PAGE_SIZE, offset, source)
      .then((data) => {
        if (isCurrent) {
          setSignalState({ status: "ready", data: data.signals, offset, source });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        setSignalState({
          status: "error",
          error: error instanceof ApiClientError ? error.kind : "unavailable",
          offset,
          source
        });
      });

    return () => {
      isCurrent = false;
    };
  }, [offset, source]);

  function selectSource(nextSource: StrategySignalSource | undefined) {
    setOffset(0);
    const params = new URLSearchParams(location.search);
    if (nextSource === undefined) {
      params.delete("source");
    } else {
      params.set("source", nextSource);
    }
    const search = params.toString();
    navigate(`${location.pathname}${search ? `?${search}` : ""}${location.hash}`, {
      replace: true
    });
  }

  return (
    <section className="page list-page signal-list-page">
      <div className="page-heading">
        <p>Signal research workspace</p>
        <h1>Signals</h1>
      </div>
      {renderSignalList(
        getSignalListState(signalState, offset, source),
        offset,
        source,
        selectSource,
        setOffset
      )}
    </section>
  );
}

function getSignalListState(
  state: SignalListState,
  offset: number,
  source: StrategySignalSource | undefined
): SignalListState {
  return state.status === "loading" || (state.offset === offset && state.source === source)
    ? state
    : { status: "loading" };
}

function renderSignalList(
  state: SignalListState,
  offset: number,
  source: StrategySignalSource | undefined,
  setSource: (source: StrategySignalSource | undefined) => void,
  setOffset: (value: number) => void
) {
  return (
    <article className="dashboard-panel">
      <div aria-label="Filter signals by source" className="signal-source-filter" role="group">
        <SourceFilterButton active={source === undefined} onClick={() => setSource(undefined)}>
          All
        </SourceFilterButton>
        {(Object.keys(SOURCE_LABELS) as StrategySignalSource[]).map((value) => (
          <SourceFilterButton active={source === value} key={value} onClick={() => setSource(value)}>
            {SOURCE_LABELS[value]}
          </SourceFilterButton>
        ))}
      </div>
      {state.status === "loading" ? (
        <FeedbackMessage variant="loading">Loading signal history.</FeedbackMessage>
      ) : state.status === "error" ? (
        <FeedbackMessage className="dashboard-alert" variant="error">
          Signal history API unavailable: {state.error}
        </FeedbackMessage>
      ) : state.data.length === 0 && offset === 0 ? (
        <EmptyState>
          {source === undefined
            ? "No successful local signal exists yet. Generate a signal from the Dashboard after market data is ready."
            : `No successful signals are available for ${SOURCE_LABELS[source]}.`}
        </EmptyState>
      ) : (
      <div className="holdings-table-wrap">
        <table className="holdings-table">
          <thead>
            <tr>
              <th scope="col">Signal</th>
              <th scope="col">Signal date</th>
              <th scope="col">Config version</th>
              <th scope="col">Result</th>
              <th scope="col">Source</th>
              <th scope="col">Generated at</th>
            </tr>
          </thead>
          <tbody>
            {state.data.map((signal) => (
              <tr key={signal.signal_id}>
                <td>
                  <Link className="operation-link" to={`/signals/${signal.signal_id}`}>
                    #{signal.signal_id}
                  </Link>
                </td>
                <td>{formatDate(signal.signal_date)}</td>
                <td>{signal.config_version}</td>
                <td>{formatNullableText(signal.result)}</td>
                <td>
                  <SourceBadge source={signal.source} />
                </td>
                <td>{formatTimestamp(signal.generated_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      )}
      {state.status === "ready" ? (
        <Pagination
          offset={offset}
          pageSize={PAGE_SIZE}
          itemCount={state.data.length}
          onOffsetChange={setOffset}
        />
      ) : null}
    </article>
  );
}

function isStrategySignalSource(value: string | null): value is StrategySignalSource {
  return value === "manual" || value === "scheduled" || value === "backtest" || value === "legacy";
}

function SourceFilterButton({
  active,
  children,
  onClick
}: {
  active: boolean;
  children: string;
  onClick: () => void;
}) {
  return (
    <button aria-pressed={active} className="signal-source-filter-button button-secondary" onClick={onClick} type="button">
      {children}
    </button>
  );
}

const SOURCE_LABELS: Record<StrategySignalSource, string> = {
  manual: "Manual",
  scheduled: "Scheduled",
  backtest: "Backtest",
  legacy: "Legacy"
};

function SourceBadge({ source }: { source: StrategySignalSource }) {
  return (
    <span
      className={`source-badge source-badge-${source}`}
      title={source === "legacy" ? "Predates provenance tracking" : undefined}
    >
      {SOURCE_LABELS[source]}
    </span>
  );
}
