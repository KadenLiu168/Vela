/*
 * Dynamic viewport verification (task 4.2).
 *
 * At a short 390x400 viewport the palette input and the active result must
 * stay reachable and the result region must scroll internally. The check is
 * pure viewport geometry (no software-keyboard simulation); mobile-device
 * manual acceptance is out of scope per user decision.
 */
import { test, expect } from "../support/test.ts";

test("palette stays reachable at a 390x400 viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 400 });
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  await page.keyboard.press("Meta+k");
  const dialog = page.locator(".command-palette-dialog");
  await expect(dialog).toBeVisible();

  await page.keyboard.type("signal");

  const geometry = await page.evaluate(() => {
    const viewportHeight = window.innerHeight;
    const dialog = document.querySelector<HTMLElement>(".command-palette-dialog")!;
    const dialogRect = dialog.getBoundingClientRect();
    const input = document.querySelector<HTMLElement>(".command-palette-input")!;
    const inputRect = input.getBoundingClientRect();
    const active = document.querySelector<HTMLElement>(".command-palette-row-active");
    const activeRect = active?.getBoundingClientRect() ?? null;
    const groupsStyle = (() => {
      const groups = document.querySelector<HTMLElement>(".command-palette-groups");
      return groups ? getComputedStyle(groups) : null;
    })();
    return {
      viewportHeight,
      dialogTop: Math.round(dialogRect.top),
      dialogBottom: Math.round(dialogRect.bottom),
      inputVisible: inputRect.top >= 0 && inputRect.bottom <= viewportHeight,
      activeVisible: activeRect
        ? activeRect.top >= 0 && activeRect.bottom <= viewportHeight
        : null,
      groupsScrollable: groupsStyle
        ? groupsStyle.overflowY === "auto" || groupsStyle.overflowY === "scroll"
        : null
    };
  });

  expect(geometry.dialogTop).toBeGreaterThanOrEqual(0);
  expect(geometry.dialogBottom).toBeLessThanOrEqual(geometry.viewportHeight);
  expect(geometry.inputVisible).toBe(true);
  expect(geometry.groupsScrollable).toBe(true);
  // The active result must be inside the visible viewport (scrollable into
  // view by the internal scroll region).
  if (geometry.activeVisible === false) {
    const scrolled = await page.evaluate(() => {
      const active = document.querySelector<HTMLElement>(".command-palette-row-active")!;
      // scrollIntoView uses the nearest scrollable ancestor: the groups region.
      active.scrollIntoView({ block: "nearest" });
      const rect = active.getBoundingClientRect();
      return rect.top >= 0 && rect.bottom <= window.innerHeight;
    });
    expect(scrolled).toBe(true);
  }
});

test("shell min-height resolves to the current viewport height", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 400 });
  await page.goto("/");
  const minHeight = await page.evaluate(() => {
    const shell = document.querySelector<HTMLElement>(".app-shell")!;
    return getComputedStyle(shell).minHeight;
  });
  expect(minHeight).toBe("400px");
});
