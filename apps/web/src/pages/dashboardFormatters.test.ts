import { expect, it } from "vitest";
import {
  formatDefensiveAssets,
  formatFailedSymbols,
  formatMomentumWindows,
  formatScoreWeights
} from "./dashboardFormatters";

it("formats dashboard strategy and market-data presentation values", () => {
  expect(formatMomentumWindows({ longWindowDays: 126, shortWindowDays: 21 })).toBe("21 / 126 days");
  expect(formatScoreWeights({ long: 0.4, short: 0.6 })).toBe("Short 0.6 / Long 0.4");
  expect(formatDefensiveAssets([{ exchange: "NYSEARCA", symbol: "SHY" }])).toBe("NYSEARCA:SHY");
  expect(formatFailedSymbols(["SPY", "QQQ"])).toBe("SPY, QQQ");
  expect(formatFailedSymbols([])).toBe("n/a");
});
