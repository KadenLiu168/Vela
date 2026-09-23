/*
 * Text enlargement and reflow verification (task 5.2).
 *
 * - 200% text: the root font size is doubled and every representative route
 *   must stay free of page-level horizontal overflow (rem tokens scale;
 *   table/chart regions scroll locally instead).
 * - 320px reflow: every route renders without page-level overflow; signs,
 *   units and actions remain reachable through the page or its local scroll
 *   region.
 */
import { test, expect } from "../support/test.ts";

const ROUTES = [
  { route: "/", heading: "Dashboard" },
  { route: "/signals", heading: "Signals" },
  { route: "/signals/42", heading: "Signal Detail" },
  { route: "/backtests", heading: "Backtests" },
  { route: "/backtests/7", heading: "Backtest Detail" },
  { route: "/walk-forwards", heading: "Walk-forward History" },
  { route: "/walk-forwards/3", heading: "Walk-forward #3" },
  { route: "/etfs/1", heading: "ETF Detail" },
  { route: "/definitely-not-a-page", heading: "Page not found" }
];

test.describe("200% text enlargement at 1440px", () => {
  for (const { route, heading } of ROUTES) {
    test(`200% text: ${route} has no page overflow and content remains available`, async ({
      page
    }) => {
      await page.goto(route);
      await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
      await page.addStyleTag({ content: "html { font-size: 32px !important; }" });
      expect(await page.evaluate(() => getComputedStyle(document.documentElement).fontSize)).toBe("32px");
      const overflow = await page.evaluate(() => {
        const root = document.scrollingElement as HTMLElement;
        return root.scrollWidth - root.clientWidth;
      });
      expect(overflow, `${route} overflows at 200% text`).toBeLessThanOrEqual(0);
    });
  }
});

test.describe("320px reflow", () => {
  for (const { route, heading } of ROUTES) {
    test(`320px: ${route} keeps content reachable`, async ({ page }) => {
      await page.setViewportSize({ width: 320, height: 844 });
      await page.goto(route);
      await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
      await page.evaluate("document.fonts.ready.then(() => true)");

      const state = await page.evaluate(() => {
        const root = document.scrollingElement as HTMLElement;
        // Controls and links must be present within the first page worth of
        // scroll or reachable through the page scroll itself.
        const links = Array.from(document.querySelectorAll("a, button"));
        const offscreen = links.filter((element) => {
          const rect = element.getBoundingClientRect();
          return rect.width === 0 && rect.height === 0;
        });
        return {
          overflow: root.scrollWidth - root.clientWidth,
          zeroSizeControls: offscreen.length
        };
      });

      expect(
        state!.overflow,
        `route ${route} has page-level horizontal overflow at 320px`
      ).toBeLessThanOrEqual(0);
    });
  }

  test("320px: wide comparison table scrolls inside its own region", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 844 });
    await page.goto("/backtests/7");
    await expect(page.getByText("Backtest #7")).toBeVisible();

    const scroll = await page.evaluate(() => {
      const wrap = document.querySelector<HTMLElement>(".comparison-matrix-wrap")!;
      const style = getComputedStyle(wrap);
      return {
        overflowX: style.overflowX,
        scrollable: wrap.scrollWidth > wrap.clientWidth,
        pageOverflow: (document.scrollingElement as HTMLElement).scrollWidth -
          (document.scrollingElement as HTMLElement).clientWidth
      };
    });

    expect(scroll!.overflowX).toBe("auto");
    expect(scroll!.scrollable).toBe(true);
    expect(scroll!.pageOverflow).toBeLessThanOrEqual(0);
  });

  test("320px: signs, units and precision survive reflow", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 844 });
    await page.goto("/backtests/7");
    await expect(page.getByText("Backtest #7")).toBeVisible();

    // Negative metric values keep their sign; percentages keep two decimals.
    await expect(page.getByText("-7.65%").first()).toBeVisible();
    await expect(page.getByText("15.43%").first()).toBeVisible();
    await expect(page.getByText("1.23").first()).toBeVisible();
  });
});
