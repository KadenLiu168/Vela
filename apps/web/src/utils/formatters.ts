export const EMPTY_VALUE = "n/a";

const numberFormatter = new Intl.NumberFormat("en-US");
const compactNumberFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 });

export function formatInteger(value: number): string {
  return numberFormatter.format(value);
}

export function formatCompactNumber(value: number): string {
  return compactNumberFormatter.format(value);
}

export function formatNullableText(value: string | null | undefined): string {
  return value ?? EMPTY_VALUE;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return EMPTY_VALUE;
  }

  return value.slice(0, 10);
}

export function formatTimestamp(value: string | null | undefined): string {
  return formatNullableText(value);
}

export function formatNullableInteger(value: number | null | undefined): string {
  return value === null || value === undefined ? EMPTY_VALUE : formatInteger(value);
}

export function formatRows(value: number | null | undefined): string {
  return value === null || value === undefined ? EMPTY_VALUE : `${formatInteger(value)} rows`;
}

export function formatBoolean(value: boolean): string {
  return value ? "Yes" : "No";
}

export function formatRatioAsPercent(value: string | null | undefined): string {
  if (value === null || value === undefined) {
    return EMPTY_VALUE;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${(parsed * 100).toFixed(2)}%` : value;
}

export function formatTargetWeight(value: string): string {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? `${trimFixed(parsed * 100, 4)}%` : value;
}

export function formatDecimal(
  value: string | null | undefined,
  digits: number,
  trimTrailingZeroes = true
): string {
  if (value === null || value === undefined) {
    return EMPTY_VALUE;
  }

  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return value;
  }

  const fixed = parsed.toFixed(digits);
  return trimTrailingZeroes ? trimFixedString(fixed) : fixed;
}

export function formatNetValue(value: number): string {
  return value.toFixed(4);
}

function trimFixed(value: number, digits: number): string {
  return trimFixedString(value.toFixed(digits));
}

function trimFixedString(value: string): string {
  return value.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
}
