import type { BacktestDetailRun } from "../api/client";
import { DescriptionItem } from "../components";
import { formatDate, formatNullableText, formatTimestamp } from "../utils/formatters";
import {
  formatParameterSummary,
  formatParametersHumanReadable
} from "./backtestFormatters";

type ExperimentConfigSectionProps = {
  run: BacktestDetailRun;
};

/**
 * Experiment Config region: the full run metadata (the first-screen summary
 * line only shows strategy, date range, and status) plus a human-readable
 * rendering of the run's execution parameters, with a closed-by-default Raw
 * Parameters disclosure preserving the original JSON.
 */
export function ExperimentConfigSection({ run }: ExperimentConfigSectionProps) {
  const parameterEntries = formatParametersHumanReadable(run.parameters_json);

  return (
    <section
      aria-labelledby="experiment-config-heading"
      className="holdings-section"
    >
      <h3 id="experiment-config-heading">Experiment config</h3>
      <dl className="compact-list config-list">
        <DescriptionItem label="Strategy" value={run.strategy_id} />
        <DescriptionItem label="Config version" value={run.config_version} />
        <DescriptionItem
          label="Date range"
          value={`${formatDate(run.start_date)} to ${formatDate(run.end_date)}`}
        />
        <DescriptionItem label="Status" value={run.status} />
        <DescriptionItem label="Started at" value={formatTimestamp(run.started_at)} />
        <DescriptionItem label="Finished at" value={formatTimestamp(run.finished_at)} />
        <DescriptionItem
          label="Error message"
          value={formatNullableText(run.error_message)}
        />
      </dl>
      {parameterEntries.length > 0 ? (
        <dl className="compact-list config-list parameter-list">
          {parameterEntries.map((entry) => (
            <DescriptionItem key={entry.key} label={entry.label} value={entry.value} />
          ))}
        </dl>
      ) : null}
      <details className="disclosure">
        <summary className="disclosure-summary">
          <h4 className="disclosure-heading" id="raw-parameters-heading">
            Raw parameters
          </h4>
        </summary>
        <div className="disclosure-body">
          <pre className="parameter-summary">{formatParameterSummary(run.parameters_json)}</pre>
        </div>
      </details>
    </section>
  );
}
