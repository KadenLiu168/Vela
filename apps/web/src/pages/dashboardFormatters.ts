import { formatCompactNumber, formatInteger, formatNullableText } from "../utils/formatters";

type MomentumWindows = {
  shortWindowDays: number;
  longWindowDays: number;
};

type ScoreWeights = {
  short: number;
  long: number;
};

type DefensiveAsset = {
  exchange: string;
  symbol: string;
};

export function formatMomentumWindows({ shortWindowDays, longWindowDays }: MomentumWindows): string {
  return `${formatInteger(shortWindowDays)} / ${formatInteger(longWindowDays)} days`;
}

export function formatScoreWeights({ short, long }: ScoreWeights): string {
  return `Short ${formatCompactNumber(short)} / Long ${formatCompactNumber(long)}`;
}

export function formatDefensiveAssets(assets: DefensiveAsset[]): string {
  return assets.map((asset) => `${asset.exchange}:${asset.symbol}`).join(", ");
}

export function formatFailedSymbols(symbols: string[]): string {
  return symbols.length > 0 ? symbols.join(", ") : formatNullableText(null);
}
