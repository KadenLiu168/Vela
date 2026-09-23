/*
 * Responsive verification (task 4.1 + 5.1 subset).
 *
 * Verifies the 1024/900/720 breakpoint boundaries (±1px), the page gutters
 * (32/24/16), panel padding (24/16), metric column counts, single-column
 * mobile layout, and the absence of page-level horizontal overflow across
 * the representative widths.
 */
import { test, expect } from "../support/test.ts";

const BREAKPOINT_WIDTHS = [1025, 1024, 1023, 901, 900, 899, 721, 720, 719];

test("shell gutters follow 32/24/16 at the breakpoint boundaries", async ({ page }) => {
  const observed: Record<number, string> = {};
  for (const width of BREAKPOINT_WIDTHS) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await expect(page.getByText("Signal #42")).toBeVisible();
    observed[width] = await page.evaluate(() => {
      const shell = document.querySelector<HTMLElement>(".app-shell")!;
      return getComputedStyle(shell).paddingLeft;
    });
  }

  expect(observed[1025]).toBe("32px");
  expect(observed[1024]).toBe("24px");
  expect(observed[1023]).toBe("24px");
  expect(observed[901]).toBe("24px");
  expect(observed[900]).toBe("24px");
  expect(observed[899]).toBe("24px");
  expect(observed[721]).toBe("24px");
  expect(observed[720]).toBe("16px");
  expect(observed[719]).toBe("16px");
});

test("standard panels stay 24px until 720px and use 16px below", async ({ page }) => {
  const observed: Record<number, string> = {};
  for (const width of [1024, 721, 720]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await expect(page.getByText("Signal #42")).toBeVisible();
    observed[width] = await page.evaluate(() => {
      const panel = document.querySelector<HTMLElement>(".dashboard-page .dashboard-panel")!;
      return getComputedStyle(panel).paddingTop;
    });
  }
  expect(observed[1024]).toBe("24px");
  expect(observed[721]).toBe("24px");
  expect(observed[720]).toBe("16px");
});

for (const width of [320, 390, 768, 1024, 1440]) {
  test(`no page-level horizontal overflow at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/");
    await expect(page.getByText("Signal #42")).toBeVisible();

    const overflow = await page.evaluate(() => {
      const root = document.scrollingElement as HTMLElement;
      return {
        scrollWidth: root.scrollWidth,
        clientWidth: root.clientWidth
      };
    });
    expect(
      overflow!.scrollWidth,
      `scrollWidth ${overflow!.scrollWidth} exceeds viewport ${overflow!.clientWidth}`
    ).toBeLessThanOrEqual(overflow!.clientWidth);
  });
}

test("research layers stack in one column at 390px", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const layout = await page.evaluate(() => {
    const layers = Array.from(document.querySelectorAll<HTMLElement>(".research-decision-path > *"));
    const tops = layers.slice(0, 4).map((layer) => Math.round(layer.getBoundingClientRect().top));
    const lefts = layers.slice(0, 4).map((layer) => Math.round(layer.getBoundingClientRect().left));
    const single = (values: number[]) => values.every((value) => value === values[0]);
    return { stacked: single(tops.slice(0, 2)) || tops[1] > tops[0], singleColumn: single(lefts) };
  });

  expect(layout!.stacked).toBe(true);
  expect(layout!.singleColumn).toBe(true);
});

test("metric rows keep two columns at 900px and one at 390px", async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 1000 });
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();
  const columns900 = await page.evaluate(() => {
    const row = document.querySelector<HTMLElement>(".metric-row");
    return row ? getComputedStyle(row).gridTemplateColumns.split(" ").length : null;
  });
  expect(columns900).toBe(2);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();
  const columns390 = await page.evaluate(() => {
    const row = document.querySelector<HTMLElement>(".metric-row");
    return row ? getComputedStyle(row).gridTemplateColumns.split(" ").length : null;
  });
  expect(columns390).toBe(1);
});
