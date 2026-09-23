/*
 * Vertical rhythm verification (task 2.3).
 *
 * Pins the shared rhythm contract via computed styles:
 *   - page heading → first content: 24px (heading-content-gap);
 *   - major research sections: 48px desktop / 32px at or below 720px;
 *   - related content groups (metrics, disclosures, grid panels): 24px;
 *   - standard panels: 24px padding both axes; panels at ≤720px: 16px.
 */
import { test, expect } from "../support/test.ts";

test("dashboard rhythm uses the shared tokens at 1440px", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const rhythm = await page.evaluate(() => {
    const heading = document.querySelector<HTMLElement>(".dashboard-page .page-heading");
    const path = document.querySelector<HTMLElement>(".research-decision-path");
    const pathStyle = path ? getComputedStyle(path) : null;
    const grid = document.querySelector<HTMLElement>(".dashboard-grid");
    const gridStyle = grid ? getComputedStyle(grid) : null;
    const panel = document.querySelector<HTMLElement>(".dashboard-page .dashboard-panel");

    // heading bottom → decision path top must be exactly the 24px gap (no
    // extra margins between them).
    let headingToContent: number | null = null;
    if (heading && path) {
      const headingBottom = heading.getBoundingClientRect().bottom;
      const contentTop = path.getBoundingClientRect().top;
      headingToContent = Math.round(contentTop - headingBottom);
    }

    // Adjacent decision-path layers must be separated by exactly the row gap
    // (bottom of one layer → top of the next), with no stacked margins.
    const layers = path ? Array.from(path.children) : [];
    const separations: number[] = [];
    for (let index = 1; index < layers.length; index += 1) {
      const previous = layers[index - 1].getBoundingClientRect().bottom;
      const current = layers[index].getBoundingClientRect().top;
      separations.push(Math.round(current - previous));
    }

    return {
      headingToContent,
      pathGap: pathStyle ? pathStyle.rowGap : null,
      layerSeparations: separations,
      gridMarginTop: gridStyle ? gridStyle.marginTop : null,
      gridGap: gridStyle ? gridStyle.columnGap : null,
      gridPadding: gridStyle ? gridStyle.paddingTop : null,
      panelPaddingTop: panel ? getComputedStyle(panel).paddingTop : null
    };
  });

  expect(rhythm.headingToContent).toBe(24);
  expect(rhythm.pathGap).toBe("48px");
  for (const separation of rhythm.layerSeparations) {
    expect(separation).toBe(48);
  }
  expect(rhythm.gridMarginTop).toBe("48px");
  expect(rhythm.gridGap).toBe("24px");
  expect(rhythm.gridPadding).toBe("24px");
  expect(rhythm.panelPaddingTop).toBe("24px");
});

test("detail sections separate by the section gap at 1440px", async ({ page }) => {
  await page.goto("/backtests/7");
  await expect(page.getByText("Backtest #7")).toBeVisible();

  const rhythm = await page.evaluate(() => {
    const decisionSummary = document.querySelector<HTMLElement>(".decision-summary-section");
    const holdings = document.querySelector<HTMLElement>(".holdings-section");
    const metricCard = document.querySelector<HTMLElement>(".detail-page .metric-card");

    return {
      decisionSummaryMargin: decisionSummary ? getComputedStyle(decisionSummary).marginTop : null,
      holdingsMargin: holdings ? getComputedStyle(holdings).marginTop : null,
      metricCardPadding: metricCard ? getComputedStyle(metricCard).paddingTop : null
    };
  });

  expect(rhythm.decisionSummaryMargin).toBe("48px");
  expect(rhythm.holdingsMargin).toBe("48px");
  expect(rhythm.metricCardPadding).toBe("24px");
});

test("dashboard rhythm is compact at 390px", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const rhythm = await page.evaluate(() => {
    const path = document.querySelector<HTMLElement>(".research-decision-path");
    const panel = document.querySelector<HTMLElement>(".dashboard-page .dashboard-panel");
    const shell = document.querySelector<HTMLElement>(".app-shell");
    return {
      pathGap: path ? getComputedStyle(path).rowGap : null,
      panelPadding: panel ? getComputedStyle(panel).paddingTop : null,
      shellPaddingX: shell ? getComputedStyle(shell).paddingLeft : null
    };
  });

  expect(rhythm.pathGap).toBe("32px");
  expect(rhythm.panelPadding).toBe("16px");
  expect(rhythm.shellPaddingX).toBe("16px");
});
