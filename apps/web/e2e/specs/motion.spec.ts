/*
 * Motion verification (task 4.3).
 *
 * - Interaction feedback uses the 120ms fast token; the palette (floating
 *   layer) may use the 200ms token.
 * - No looping or decorative entrance animation runs (skeleton is a static
 *   placeholder; textual loading feedback remains).
 * - Under prefers-reduced-motion every element and pseudo-element gets
 *   zero-duration transitions/animations.
 */
import { test, expect } from "../support/test.ts";

test("interaction feedback transitions use the 120ms token", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const durations = await page.evaluate(() => {
    const read = (selector: string) => {
      const element = document.querySelector<HTMLElement>(selector);
      if (element === null) {
        return null;
      }
      // Multi-property transitions report a comma list; every entry must use
      // the fast token.
      return getComputedStyle(element).transitionDuration
        .split(",")
        .map((value) => value.trim());
    };
    return {
      button: read(".button-secondary"),
      navLink: read(".app-nav-link")
    };
  });

  for (const value of [durations.button, durations.navLink]) {
    for (const entry of value!) {
      expect(entry).toBe("0.12s");
    }
  }

  // The palette (floating layer) rows may use the 200ms token at most.
  await page.keyboard.press("Meta+k");
  const paletteRow = await page.evaluate(() => {
    const element = document.querySelector<HTMLElement>(".command-palette-row");
    if (element === null) {
      return null;
    }
    return getComputedStyle(element)
      .transitionDuration.split(",")
      .map((value) => value.trim());
  });
  if (paletteRow) {
    for (const entry of paletteRow) {
      expect(["0.12s", "0.2s"]).toContain(entry);
    }
  }
});

test("reduced motion zeroes transitions on elements and pseudo-elements", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/backtests/7");
  await expect(page.getByText("Backtest #7")).toBeVisible();
  await expect(page.locator(".detail-page .disclosure-summary").first()).toBeVisible();

  const reduced = await page.evaluate(() => {
    const read = (selector: string, pseudo: string | null = null) => {
      const element = document.querySelector<HTMLElement>(selector);
      return element
        ? getComputedStyle(element, pseudo).transitionDuration
        : null;
    };
    return {
      link: read(".detail-page .detail-back-link"),
      pseudoElement: read(".detail-page .disclosure-summary", "::before")
    };
  });

  expect(reduced.link).toBe("0s");
  expect(reduced.pseudoElement).toBe("0s");
});

test("loading feedback remains available without skeleton pulsing", async ({ page }) => {
  await page.goto("/");
  const skeleton = await page.evaluate(() => {
    const skeletonElement = document.querySelector<HTMLElement>(".skeleton-pulse");
    if (skeletonElement === null) {
      return { present: false, animationName: null };
    }
    return {
      present: true,
      animationName: getComputedStyle(skeletonElement).animationName
    };
  });

  if (skeleton!.present) {
    expect(skeleton!.animationName).toBe("none");
  }

  // Route-level loading feedback carries a textual status announcement.
  await page.goto("/backtests/8");
  const status = page.getByRole("status");
  await expect(status.first()).toBeVisible();
});

test("reduced motion is honored on a detail page with disclosure content", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/backtests/7");
  await expect(page.getByText("Backtest #7")).toBeVisible();
  await expect(page.locator(".detail-page .disclosure-summary").first()).toBeVisible();

  const durations = await page.evaluate(() => {
    const read = (selector: string) => {
      const element = document.querySelector<HTMLElement>(selector);
      return element ? getComputedStyle(element).transitionDuration : null;
    };
    return {
      summary: read(".detail-page .disclosure-summary"),
      input: read(".backtest-run-form input")
    };
  });
  // Elements that declare no transition report "auto"/"0s"; the key assertion
  // is that nothing carries a non-zero duration.
  for (const value of Object.values(durations)) {
    expect(value === null || value === "0s").toBe(true);
  }
});
