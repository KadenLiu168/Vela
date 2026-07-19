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
