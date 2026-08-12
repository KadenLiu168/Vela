import type { BacktestBenchmark } from "../api/client";
import { formatDate, formatNetValue, formatNullableText } from "../utils/formatters";

type EquityCurvePointReadout = {
  tradeDate: string;
  netValue: number;
};

export function formatParameterSummary(value: string | null): string {
  if (!value) {
    return formatNullableText(value);
  }

  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}

export function formatEquityCurvePoint(point: EquityCurvePointReadout): string {
  return `${formatDate(point.tradeDate)} / ${formatNetValue(point.netValue)}`;
}

/** Parses an API metric string into a finite number, or null when the value is
 *  null or non-numeric. Shared by the difference helpers and the Decision
 *  Summary difference evidence. */
export function parseMetricNumber(value: string | null): number | null {
  if (value === null) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Display arithmetic on API-provided non-null values (strategy minus
 *  benchmark). This is never financial derivation: the inputs are numbers the
 *  backend already published, and the result is only rendered as difference
 *  evidence. Null or non-finite inputs propagate to null. */
export function computeMetricDifference(
  strategyValue: string | null,
  benchmarkValue: string | null
): number | null {
  const strategy = parseMetricNumber(strategyValue);
  const benchmark = parseMetricNumber(benchmarkValue);
  if (strategy === null || benchmark === null) {
    return null;
  }
  return strategy - benchmark;
}

export type Verdict = "Outperforming" | "Underperforming" | "Mixed";

/** Sign-based verdict over strategy-vs-benchmark differences.
 *
 * A difference is valid when it is a finite number. The verdict is withheld
 * (null) unless at least two valid differences are present; it is never a
 * weighted score, only a translation of the difference signs into plain
 * language:
 *   - all >= 0 with at least one > 0           -> Outperforming
 *   - all <= 0 with at least one < 0           -> Underperforming
 *   - any other sign mix (including all-zero)  -> Mixed
 */
export function computeVerdict(differences: (number | null)[]): Verdict | null {
  const valid = differences.filter((value): value is number => value !== null);
  if (valid.length < 2) {
    return null;
  }
  const hasPositive = valid.some((value) => value > 0);
  const hasNegative = valid.some((value) => value < 0);
  if (hasPositive && !hasNegative) {
    return "Outperforming";
  }
  if (hasNegative && !hasPositive) {
    return "Underperforming";
  }
  return "Mixed";
}

/** Primary benchmark for Decision Summary difference evidence: the CSI-300
 *  buy-and-hold key when present, otherwise the first benchmark in the API
 *  collection, otherwise null (no benchmarks). */
export function resolvePrimaryBenchmark(
  benchmarks: BacktestBenchmark[]
): BacktestBenchmark | null {
  if (benchmarks.length === 0) {
    return null;
  }
  return (
    benchmarks.find((benchmark) => benchmark.key === "csi_300_buy_hold") ??
    benchmarks[0]
  );
}

export type ParameterEntry = {
  key: string;
  label: string;
  value: string;
};

const METRIC_VERSION_KEYS = [
  "performance_metric_version",
  "equity_model_version",
  "tail_distribution_metric_version",
  "benchmark_regime_metric_version"
] as const;

const METRIC_VERSION_LABELS: Record<string, string> = {
  performance_metric_version: "Performance metric version",
  equity_model_version: "Equity model version",
  tail_distribution_metric_version: "Tail distribution metric version",
  benchmark_regime_metric_version: "Benchmark regime metric version"
};

const KNOWN_PARAMETER_ORDER = [
  "strategy_id",
  "config_version",
  "type",
  "start_date",
  "end_date",
  "risk_free_rate",
  ...METRIC_VERSION_KEYS
];

/** Human-readable key-value rendering of the run's flat execution parameters.
 *  Known keys use the documented label/format mapping; unknown keys fall back
 *  to their raw key and value text. Returns [] for null, malformed, or
 *  non-object payloads. */
export function formatParametersHumanReadable(
  parametersJson: string | null
): ParameterEntry[] {
  if (!parametersJson) {
    return [];
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(parametersJson);
  } catch {
    return [];
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return [];
  }

  const record = parsed as Record<string, unknown>;
  const known = KNOWN_PARAMETER_ORDER.filter((key) => key in record).map((key) =>
    formatParameterEntry(key, record[key])
  );
  const unknown = Object.keys(record)
    .filter((key) => !KNOWN_PARAMETER_ORDER.includes(key))
    .map((key) => formatParameterEntry(key, record[key]));

  return [...known, ...unknown];
}

function formatParameterEntry(key: string, rawValue: unknown): ParameterEntry {
  switch (key) {
    case "strategy_id":
      return { key, label: "Strategy", value: textValue(rawValue) };
    case "config_version":
      return { key, label: "Config version", value: textValue(rawValue) };
    case "type":
      return {
        key,
        label: "Strategy type",
        value: humanizeSnakeCase(textValue(rawValue))
      };
    case "start_date":
      return { key, label: "Start date", value: formatDate(textValue(rawValue)) };
    case "end_date":
      return { key, label: "End date", value: formatDate(textValue(rawValue)) };
    case "risk_free_rate":
      return {
        key,
        label: "Annualized risk-free rate",
        value: formatRiskFreeRate(rawValue)
      };
    default:
      if (METRIC_VERSION_KEYS.includes(key as (typeof METRIC_VERSION_KEYS)[number])) {
        return { key, label: METRIC_VERSION_LABELS[key], value: textValue(rawValue) };
      }
      return { key, label: key, value: textValue(rawValue) };
  }
}

function textValue(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}

/** snake_case -> sentence case ("dual_momentum" -> "Dual momentum"). */
function humanizeSnakeCase(value: string): string {
  const human = value.replace(/_/g, " ").replace(/\s+/g, " ").trim();
  return human.length === 0 ? human : human[0].toUpperCase() + human.slice(1);
}

/** Annualized rate as a percentage (0.02 -> "2.0%"); non-numeric values fall
 *  back to their raw text. */
function formatRiskFreeRate(value: unknown): string {
  const parsed =
    typeof value === "number"
      ? value
      : typeof value === "string"
        ? Number(value)
        : NaN;
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(1)}%` : textValue(value);
}
