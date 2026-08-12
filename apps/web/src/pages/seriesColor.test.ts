import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { seriesColor, SERIES_COLOR_BY_KEY } from "./seriesColor";

const TOKENS_CSS = readFileSync(join(__dirname, "../styles/tokens.css"), "utf8");

/** Resolves a var(...) reference chain declared in tokens.css to a #rrggbb hex. */
function resolveToken(name: string): string {
  const bareName = name.replace(/^--/, "");
  const declaration = TOKENS_CSS.match(new RegExp(`--${bareName}:\\s*([^;]+);`));
  expect(declaration, `--${bareName} must be declared in tokens.css`).not.toBeNull();
  const raw = declaration![1].trim();
  if (raw.startsWith("#")) {
    return raw;
  }
  const reference = raw.match(/var\((--[\w-]+)\)/);
  expect(reference, `--${bareName} resolves through a var() reference`).not.toBeNull();
  return resolveToken(reference![1]);
}

function parseHex(hex: string): [number, number, number] {
  const normalized = hex.replace(/^#/, "");
  return [
    parseInt(normalized.slice(0, 2), 16),
    parseInt(normalized.slice(2, 4), 16),
    parseInt(normalized.slice(4, 6), 16)
  ];
}

function relativeLuminance(hex: string): number {
  const [r, g, b] = parseHex(hex).map((channel) => {
    const s = channel / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrastRatio(foreground: string, background: string): number {
  const lighter = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const darker = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (lighter + 0.05) / (darker + 0.05);
}

describe("categorical series tokens", () => {
  const expectedSeriesValues = {
    "color-series-1": "#e4f222", // var(--color-acid-lime)
    "color-series-2": "#02b8cc", // var(--color-signal-teal)
    "color-series-3": "#4f8cff",
    "color-series-4": "#eb5757", // var(--color-coral-red)
    "color-series-5": "#f2b84b",
    "color-series-6": "#d96bd8"
  };

  it("declares the six exact categorical series tokens in the :root block", () => {
    const rootBlock = TOKENS_CSS.match(/:root\s*{([\s\S]*?)}/);
    expect(rootBlock).not.toBeNull();

    for (const [token, expected] of Object.entries(expectedSeriesValues)) {
      expect(resolveToken(token)).toBe(expected);
      expect(rootBlock![1]).toContain(`--${token}:`);
    }
  });

  it("lists the categorical series group in the leading token catalog", () => {
    const catalog = TOKENS_CSS.slice(0, TOKENS_CSS.indexOf(":root"));
    expect(catalog).toMatch(/categorical series/i);
  });

  it("declares each series token only inside tokens.css", () => {
    const declarations = TOKENS_CSS.match(/--color-series-\d:\s*[^;]+;/g);
    expect(declarations?.length).toBe(6);
  });

  it.each(Object.entries(expectedSeriesValues))(
    "meets WCAG AA normal-text contrast for %s on --surface-obsidian",
    (_token, hex) => {
      // --surface-obsidian resolves to --color-obsidian (#161718).
      const obsidian = resolveToken("surface-obsidian");
      expect(obsidian).toBe("#161718");
      expect(contrastRatio(hex, obsidian)).toBeGreaterThanOrEqual(4.5);
    }
  );
});

describe("seriesColor(key)", () => {
  it("maps the three current supported keys to distinct explicit tokens", () => {
    expect(seriesColor("strategy")).toBe("var(--color-series-1)");
    expect(seriesColor("equal_weight_monthly")).toBe("var(--color-series-2)");
    expect(seriesColor("csi_300_buy_hold")).toBe("var(--color-series-3)");
    expect(new Set(Object.values(SERIES_COLOR_BY_KEY)).size).toBe(3);
  });

  it("keeps identity stable when another series is absent", () => {
    // Same keys in different orders / with a missing sibling resolve identically.
    expect(seriesColor("strategy")).toBe(seriesColor("strategy"));
    expect(seriesColor("equal_weight_monthly")).toBe(seriesColor("equal_weight_monthly"));
    expect(seriesColor("csi_300_buy_hold")).toBe(seriesColor("csi_300_buy_hold"));
    expect(seriesColor("strategy")).not.toBe(seriesColor("csi_300_buy_hold"));
  });

  it("resolves unknown keys to a deterministic reserved-role fallback", () => {
    const first = seriesColor("unknown_series");
    const second = seriesColor("unknown_series");
    expect(first).toBe(second);
    expect(first).toMatch(/var\(--color-series-[456]\)/);
  });

  it("does not fall back onto a current identity token", () => {
    expect(seriesColor("unknown_series")).not.toBe("var(--color-series-1)");
    expect(seriesColor("unknown_series")).not.toBe("var(--color-series-2)");
    expect(seriesColor("unknown_series")).not.toBe("var(--color-series-3)");
  });
});
