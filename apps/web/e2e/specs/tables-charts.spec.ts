/*
 * Table and chart detail verification (task 3.5).
 *
 * - Numeric cells align right; name cells stay left and wrap; Mono cells
 *   keep their one-line shape.
 * - Wide-table scroll regions are named, keyboard-reachable and show a
 *   visible focus outline.
 * - Equity-curve series carry stable line styles synced with the legend.
 */
import { test, expect } from "../support/test.ts";

test("dashboard holdings table aligns quantities right and wraps names", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const table = await page.evaluate(() => {
    const table = document.querySelector<HTMLElement>(".signal-panel .holdings-table");
    if (table === null) {
      return null;
    }
    const nameCell = table.querySelector<HTMLElement>("tbody td:nth-child(2)");
    const weightCell = table.querySelector<HTMLElement>("tbody td:nth-child(3)");
    return {
      nameAlign: nameCell ? getComputedStyle(nameCell).textAlign : null,
      nameWhiteSpace: nameCell ? getComputedStyle(nameCell).whiteSpace : null,
      weightAlign: weightCell ? getComputedStyle(weightCell).textAlign : null,
      monoWhiteSpace: getComputedStyle(
        table.querySelector<HTMLElement>("tbody td.mono-compact")!
      ).whiteSpace
    };
  });

  expect(table).not.toBeNull();
  expect(table!.nameAlign).toBe("left");
  expect(table!.nameWhiteSpace).toBe("normal");
  expect(table!.weightAlign).toBe("right");
  expect(table!.monoWhiteSpace).toBe("nowrap");
});

test("holdings table scroll regions are named keyboard-reachable regions", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const region = await page.evaluate(() => {
    const wrap = document.querySelector<HTMLElement>(".signal-panel .holdings-table-wrap");
    if (wrap === null) {
      return null;
    }
    return {
      role: wrap.getAttribute("role"),
      label: wrap.getAttribute("aria-label"),
      tabIndex: wrap.getAttribute("tabindex")
    };
  });
  expect(region!.role).toBe("region");
  expect(region!.label).toBeTruthy();
  expect(region!.tabIndex).toBe("0");
});

test("table wrap shows a visible focus outline on keyboard focus", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  await page.keyboard.press("Tab"); // skip link
  const outline = await page.evaluate(() => {
    const wrap = document.querySelector<HTMLElement>(".signal-panel .holdings-table-wrap");
    wrap?.focus();
    return wrap ? getComputedStyle(wrap).outlineStyle : null;
  });
  // Focus the wrap programmatically: :focus-visible applies for keyboard focus.
  expect(outline).toBe("solid");
});

test("equity-curve series line styles sync with legend swatches", async ({ page }) => {
  await page.goto("/backtests/7");
  await expect(page.getByText("Backtest #7")).toBeVisible();

  const styles = await page.evaluate(() => {
    const readLine = (key: string) => {
      const line = document.querySelector<SVGPathElement>(`[data-testid="equity-curve-line-${key}"]`);
      return line
        ? { stroke: line.getAttribute("stroke"), dash: line.getAttribute("stroke-dasharray") }
        : null;
    };
    const swatch = (key: string) => {
      const swatch = document.querySelector<SVGLineElement>(`[data-testid="equity-curve-swatch-${key}"]`);
      return swatch
        ? { stroke: swatch.getAttribute("stroke"), dash: swatch.getAttribute("stroke-dasharray") }
        : null;
    };
    return {
      strategy: { line: readLine("strategy"), swatch: swatch("strategy") },
      equal: { line: readLine("equal_weight_monthly"), swatch: swatch("equal_weight_monthly") },
      csi: { line: readLine("csi_300_buy_hold"), swatch: swatch("csi_300_buy_hold") }
    };
  });

  // Strategy: solid line.
  expect(styles.strategy!.line!.dash).toBeNull();
  expect(styles.strategy!.swatch!.dash).toBeNull();
  // Benchmarks get distinct dash patterns, identical to their swatches.
  expect(styles.equal!.line!.dash).toBe(styles.equal!.swatch!.dash);
  expect(styles.csi!.line!.dash).toBe(styles.csi!.swatch!.dash);
  expect(styles.equal!.line!.dash).not.toBe(styles.csi!.line!.dash);
  // Colors stay keyed (not positional).
  expect(styles.strategy!.line!.stroke).toBe("var(--chart-series-1)");
  expect(styles.equal!.line!.stroke).toBe("var(--chart-series-2)");
  expect(styles.csi!.line!.stroke).toBe("var(--chart-series-3)");
});
