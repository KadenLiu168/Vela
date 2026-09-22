import { useEffect, useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  type StrategySignalListItem,
  type StrategySignalSource,
  listStrategySignals
} from "../api/client";
import { EmptyState, FeedbackMessage, Pagination, ReadFailure } from "../components";
import { SOURCE_LABELS } from "./signalSourceLabels";
import { useDocumentTitle } from "../utils/documentTitle";
import { isValidListOffset, listHrefWith, listOffsetFrom } from "../utils/listQuery";
import { useResource, type LoadableResourceState } from "../utils/useResource";
import { formatDate, formatNullableText, formatTimestamp } from "../utils/formatters";

const PAGE_SIZE = 20;

export function SignalListPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const rawSource = searchParams.get("source");
  const rawOffset = searchParams.get("offset");
  const source = isStrategySignalSource(rawSource) ? rawSource : undefined;
  const offset = listOffsetFrom(rawOffset);
  const listHref = `${location.pathname}${location.search}`;
  const { state: signalState, reload } = useResource({
    key: `${offset}:${source ?? ""}`,
    load: () => listStrategySignals(PAGE_SIZE, offset, source).then((data) => data.signals)
  });

  useDocumentTitle("Signals");

  // Normalize an invalid source value through Router replacement navigation,
  // preserving unrelated query parameters and the hash.
  useEffect(() => {
    if (rawSource !== null && !isStrategySignalSource(rawSource)) {
      navigate(listHrefWith(location, { source: null }), { replace: true });
    }
  }, [rawSource, location, navigate]);

  // Normalize an invalid offset the same way: only `offset` is removed.
  useEffect(() => {
    if (rawOffset !== null && !isValidListOffset(rawOffset)) {
      navigate(listHrefWith(location, { offset: null }), { replace: true });
    }
  }, [rawOffset, location, navigate]);

  function selectSource(nextSource: StrategySignalSource | undefined) {
    navigate(listHrefWith(location, { source: nextSource ?? null, offset: null }), { replace: true });
  }

  function selectOffset(nextOffset: number) {
    const next = Math.max(0, nextOffset);
    navigate(listHrefWith(location, { offset: next === 0 ? null : String(next) }));
  }

  return (
    <section className="page list-page signal-list-page">
      <div className="page-heading">
        <p>Signal research workspace</p>
        <h1>Signals</h1>
      </div>
      {renderSignalList(
        signalState,
        offset,
        source,
        selectSource,
        selectOffset,
        reload,
        listHref
      )}
    </section>
  );
}


function renderSignalList(
  state: LoadableResourceState<StrategySignalListItem[]>,
  offset: number,
  source: StrategySignalSource | undefined,
  setSource: (source: StrategySignalSource | undefined) => void,
  setOffset: (value: number) => void,
  retry: () => void,
  listHref: string
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
        <ReadFailure error={state.error} label="Signal history" onRetry={retry} />
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
                <td className="mono-compact">
                  <Link
                    className="operation-link"
                    state={{ listHref }}
                    to={`/signals/${signal.signal_id}`}
                  >
                    #{signal.signal_id}
                  </Link>
                </td>
                <td className="mono-compact">{formatDate(signal.signal_date)}</td>
                <td className="mono-compact">{signal.config_version}</td>
                <td>{formatNullableText(signal.result)}</td>
                <td>
                  <SourceBadge source={signal.source} />
                </td>
                <td className="mono-compact">{formatTimestamp(signal.generated_at)}</td>
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
