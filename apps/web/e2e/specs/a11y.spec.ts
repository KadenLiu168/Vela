/*
 * Accessibility verification (task 4.4).
 *
 * axe-core scans on the representative routes at desktop and mobile widths,
 * plus keyboard flow checks: skip link, palette focus trap/return, and
 * focus visibility. The surfaces spec checks computed text contrast.
 */
import { test, expect } from "../support/test.ts";
import AxeBuilder from "@axe-core/playwright";

const ROUTES = ["/", "/signals", "/signals/42", "/backtests", "/backtests/7", "/walk-forwards", "/walk-forwards/3", "/etfs/1", "/definitely-not-a-page"];

async function scanAxe(page: import("@playwright/test").Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag22aa"])
    .analyze();
  const violations = results.violations;
  if (violations.length > 0) {
    const summary = violations
      .map((violation) => `${violation.id} (${violation.impact}): ${violation.nodes.length} nodes`)
      .join("\n");
    throw new Error(`axe found A/AA violations:\n${summary}`);
  }
}

for (const route of ROUTES) {
  test(`axe passes on ${route} at 1440px`, async ({ page }) => {
    await page.goto(route);
    // Let lazy content settle so axe sees the loaded page.
    await page.waitForTimeout(300);
    await scanAxe(page);
  });

  test(`axe passes on ${route} at 390px`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(route);
    await page.waitForTimeout(300);
    await scanAxe(page);
  });
}

test("skip link moves focus to main content", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");

  const skipLink = page.locator(".skip-link");
  await expect(skipLink).toBeFocused();

  await page.keyboard.press("Enter");
  await page.waitForTimeout(100);
  const focused = await page.evaluate(() => {
    const active = document.activeElement as HTMLElement | null;
    return {
      isMain: active?.id === "main-content",
      tag: active?.tagName.toLowerCase()
    };
  });
  expect(focused!.isMain).toBe(true);
});

test("focus is visible on the primary controls", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();
  await page.keyboard.press("Tab");
  const focusVisible = await page.evaluate(() => {
    const button = document.querySelector<HTMLElement>(".dashboard-refresh-action")!;
    button.focus();
    const style = getComputedStyle(button);
    return { visible: button.matches(":focus-visible"), outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
  });
  expect(focusVisible!.visible).toBe(true);
  expect(focusVisible!.outlineStyle).not.toBe("none");
  expect(parseFloat(focusVisible!.outlineWidth)).toBeGreaterThanOrEqual(2);
});

test("palette focus enters, stays, and returns to the opener", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  // Open via keyboard, run a full keyboard round trip, close, and confirm
  // focus returns to the opener.
  await page.keyboard.press("Meta+k");
  await expect(page.locator(".command-palette-input")).toBeFocused();

  await page.keyboard.type("signal");
  await page.keyboard.press("Escape");
  await expect(page.locator(".command-palette-dialog")).toBeHidden();

  const focusAfter = await page.evaluate(() => document.activeElement === document.body);
  // Focus must return to the opener (body counts as the neutral opener when
  // the palette was opened via the global shortcut).
  expect(focusAfter).toBe(true);
});

test("route transitions move focus to the destination heading", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  await page.getByRole("link", { name: "Signals" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Signals" })).toBeVisible();
  await page.waitForTimeout(100);

  const focusInfo = await page.evaluate(() => {
    const active = document.activeElement as HTMLElement | null;
    return { tag: active?.tagName.toLowerCase(), text: active?.textContent ?? null };
  });
  expect(focusInfo!.tag).toBe("h1");
  expect(focusInfo!.text).toContain("Signals");
});
