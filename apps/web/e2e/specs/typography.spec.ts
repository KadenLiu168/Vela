/*
 * Typography role verification (task 2.2).
 *
 * Verifies against computed styles:
 *   - every page that renders `.page-heading h1` shares the same title role
 *     at a given viewport (36/40 desktop, 28/36 at or below 720px);
 *   - promoted status/evidence text uses at least the dense role (13/20);
 *   - the compact-list baseline (labels 11/20, values 13/20) is unchanged.
 */
import { test, expect } from "../support/test.ts";

const SHARED_PAGES = ["/", "/signals", "/backtests", "/walk-forwards", "/signals/42", "/backtests/7", "/walk-forwards/3", "/etfs/1", "/definitely-not-a-page"];

async function headingStyle(page: import("@playwright/test").Page, path: string) {
  await page.goto(path);
  const h1 = page.locator(".page-heading h1").first();
  await expect(h1).toBeVisible();
  return page.evaluate(() => {
    const element = document.querySelector<HTMLElement>(".page-heading h1");
    const computed = getComputedStyle(element!);
    return { fontSize: computed.fontSize, lineHeight: computed.lineHeight };
  });
}

test("page-title role is identical across pages at 1440px", async ({ page }) => {
  const sizes = new Set<string>();

  for (const path of SHARED_PAGES) {
    const style = await headingStyle(page, path);
    sizes.add(`${style.fontSize}/${style.lineHeight}`);
  }

  expect([...sizes]).toEqual(["36px/40px"]);
});

test("page-title role is identical and compact at 390px", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const sizes = new Set<string>();

  for (const path of SHARED_PAGES) {
    const style = await headingStyle(page, path);
    sizes.add(`${style.fontSize}/${style.lineHeight}`);
  }

  expect([...sizes]).toEqual(["28px/36px"]);
});

test("brand stays smaller than the page title at both roles", async ({ page }) => {
  await page.goto("/");
  const brand = await page.evaluate(() => {
    const brandTitle = document.querySelector<HTMLElement>(".app-brand-title");
    return brandTitle ? getComputedStyle(brandTitle).fontSize : null;
  });
  expect(brand).toBe("22px");

  await page.setViewportSize({ width: 390, height: 844 });
  const brandCompact = await page.evaluate(() => {
    const brandTitle = document.querySelector<HTMLElement>(".app-brand-title");
    return brandTitle ? getComputedStyle(brandTitle).fontSize : null;
  });
  expect(brandCompact).toBe("22px");
});

test("status pill renders at least the dense role", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  await expect(page.locator(".status-pill").first()).toBeVisible();
  const pill = await page.evaluate(() => {
    const pillElement = document.querySelector<HTMLElement>(".status-pill");
    const computed = getComputedStyle(pillElement!);
    return { fontSize: computed.fontSize, lineHeight: computed.lineHeight };
  });
  expect(Number.parseFloat(pill.fontSize)).toBeGreaterThanOrEqual(13);
  expect(Number.parseFloat(pill.lineHeight)).toBeGreaterThanOrEqual(20);
});

test("dashboard load state renders at least the dense role", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".dashboard-load-state")).toBeVisible();
  const loadState = await page.evaluate(() => {
    const element = document.querySelector<HTMLElement>(".dashboard-load-state");
    return getComputedStyle(element!).fontSize;
  });
  expect(Number.parseFloat(loadState)).toBeGreaterThanOrEqual(13);
});

test("compact-list baseline stays 11/20 labels and 13/20 values", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".compact-list dt").first()).toBeVisible();
  const baseline = await page.evaluate(() => {
    const dt = document.querySelector<HTMLElement>(".compact-list dt");
    const dd = document.querySelector<HTMLElement>(".compact-list dd");
    return {
      dt: getComputedStyle(dt!),
      dd: getComputedStyle(dd!)
    };
  });
  expect(baseline.dt.fontSize).toBe("11px");
  expect(baseline.dt.lineHeight).toBe("20px");
  expect(baseline.dd.fontSize).toBe("13px");
  expect(baseline.dd.lineHeight).toBe("20px");
});

test("etf-row date values use at least the label role", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".etf-row-date").first()).toBeVisible();
  const date = await page.evaluate(() => {
    const element = document.querySelector<HTMLElement>(".etf-row-date");
    return getComputedStyle(element!).fontSize;
  });
  expect(Number.parseFloat(date)).toBeGreaterThanOrEqual(12);
});
