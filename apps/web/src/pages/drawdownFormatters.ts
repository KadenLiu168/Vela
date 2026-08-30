import { formatDate } from "../utils/formatters";

export type DrawdownMetrics = {
  longest_drawdown_duration_sessions: number | null;
  longest_drawdown_peak_date: string | null;
  longest_drawdown_trough_date: string | null;
  longest_drawdown_recovery_date: string | null;
};

export function formatDrawdownRecovery(metrics: DrawdownMetrics): string {
  if (metrics.longest_drawdown_recovery_date) {
    return formatDate(metrics.longest_drawdown_recovery_date);
  }

  return metrics.longest_drawdown_duration_sessions !== null &&
    metrics.longest_drawdown_duration_sessions > 0 &&
    metrics.longest_drawdown_peak_date !== null &&
    metrics.longest_drawdown_trough_date !== null
    ? "ongoing"
    : "n/a";
}
