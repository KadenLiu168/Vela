/*
 * Surface role verification (task 3.1).
 *
 * Ordinary research panels use the panel surface; emphasized metric tiles and
 * metric cards keep the raised surface; panels carry no shadow; the Command
 * Palette keeps its floating shadow-xl elevation.
 */
import { test, expect } from "../support/test.ts";

function toHex(rgb: string | null): string | null {
  if (rgb === null) {
    return null;
  }
  const match = rgb.match(/rgba?\((\d+), (\d+), (\d+)/);
  if (match === null) {
    return rgb;
  }
  const hex = (value: number) => value.toString(16).padStart(2, "0");
  return `#${hex(Number(match[1]))}${hex(Number(match[2]))}${hex(Number(match[3]))}`;
}

function contrastRatio(foreground: string, background: string): number {
  const luminance = (color: string) => {
    const channels = color.match(/\d+(?:\.\d+)?/g)?.slice(0, 3).map(Number);
    if (channels?.length !== 3) throw new Error(`Unsupported computed color: ${color}`);
    const [red, green, blue] = channels.map((value) => {
      const scaled = value / 255;
      return scaled <= 0.04045 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4;
    });
    return red * 0.2126 + green * 0.7152 + blue * 0.0722;
  };
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test("panel surfaces use the panel role; metrics stay raised; palette floats", async ({
  page
}) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const surfaces = await page.evaluate(() => {
    const read = (selector: string) => {
      const element = document.querySelector<HTMLElement>(selector);
      return element ? getComputedStyle(element).backgroundColor : null;
    };
    const readShadow = (selector: string) => {
      const element = document.querySelector<HTMLElement>(selector);
      return element ? getComputedStyle(element).boxShadow : null;
    };
    return {
      signalPanel: read(".signal-panel"),
      marketPanel: read(".market-panel"),
      metricTile: read(".metric"),
      headlineCard: read(".research-headline"),
      paletteShadow: readShadow(".command-palette-dialog"),
      panelShadow: readShadow(".signal-panel")
    };
  });

  // --surface-panel = #0f141d; --surface-raised = #151c28.
  expect(toHex(surfaces.signalPanel)).toBe("#0f141d");
  expect(toHex(surfaces.marketPanel)).toBe("#0f141d");
  expect(toHex(surfaces.metricTile)).toBe("#151c28");
  expect(toHex(surfaces.headlineCard)).toBe("#151c28");
  expect(surfaces.paletteShadow).not.toBe("none");
  expect(surfaces.panelShadow).toBe("none");
});

test("text contrast holds on the panel and raised surfaces", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  // Computed colors of the dense label/value pair on the panel surface.
  const contrast = await page.evaluate(() => {
    const label = document.querySelector<HTMLElement>(".compact-list dt");
    const value = document.querySelector<HTMLElement>(".compact-list dd");
    const panel = label?.closest<HTMLElement>(".dashboard-panel");
    return {
      labelColor: label ? getComputedStyle(label).color : null,
      valueColor: value ? getComputedStyle(value).color : null,
      panelColor: panel ? getComputedStyle(panel).backgroundColor : null
    };
  });

  expect(contrast.labelColor).not.toBeNull();
  expect(contrast.valueColor).not.toBeNull();
  // --text-tertiary (#7f8a9a) on --surface-panel (#0f141d) is ~4.9:1 (AA);
  // --text-primary (#f4f7fb) on panel is far above it.
  expect(contrast.labelColor).toBe("rgb(127, 138, 154)");
  expect(contrast.valueColor).toBe("rgb(244, 247, 251)");
  expect(toHex(contrast.panelColor)).toBe("#0f141d");
  expect(contrastRatio(contrast.labelColor!, contrast.panelColor!)).toBeGreaterThanOrEqual(4.5);
  expect(contrastRatio(contrast.valueColor!, contrast.panelColor!)).toBeGreaterThanOrEqual(4.5);
});
