import type { StrategySignalSource } from "../api/client";

/** Display labels for a strategy signal's provenance. Shared by the Signals
 *  list and the Dashboard decision path so both surfaces name a source the
 *  same way. */
export const SOURCE_LABELS: Record<StrategySignalSource, string> = {
  manual: "Manual",
  scheduled: "Scheduled",
  backtest: "Backtest",
  legacy: "Legacy"
};

/** Display label for a persisted source value, falling back to the raw value
 *  when an unknown source reaches the client. */
export function sourceLabel(source: string): string {
  return SOURCE_LABELS[source as StrategySignalSource] ?? source;
}
