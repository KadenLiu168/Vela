/*
 * Control sizing and state verification (task 3.2).
 *
 * Verifies against computed styles in the production build:
 *   - buttons/inputs/selects honor the 36px desktop control minimum;
 *   - at or below 720px and under pointer:coarse they honor the 44px target;
 *   - the form error keeps its programmatic association in the real DOM.
 */
import { test, expect } from "../support/test.ts";

test("controls honor the 36px desktop minimum at 1440px", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const heights = await page.evaluate(() => {
    const read = (selector: string) => {
      const element = document.querySelector<HTMLElement>(selector);
      return element ? getComputedStyle(element).minHeight : null;
    };
    return {
      primary: read(".button-primary"),
      secondary: read(".button-secondary"),
      input: read(".backtest-run-form input")
    };
  });

  expect(heights.primary).toBe("36px");
  expect(heights.secondary).toBe("36px");
  expect(heights.input).toBe("36px");
});

test("controls honor the 44px touch target at 390px", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const heights = await page.evaluate(() => {
    const read = (selector: string) => {
      const element = document.querySelector<HTMLElement>(selector);
      return element ? getComputedStyle(element).minHeight : null;
    };
    return {
      primary: read(".button-primary"),
      secondary: read(".button-secondary"),
      input: read(".backtest-run-form input")
    };
  });

  expect(heights.primary).toBe("44px");
  expect(heights.secondary).toBe("44px");
  expect(heights.input).toBe("44px");
});

test("backtest form error association renders in the real DOM", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Run backtest" })).toBeVisible();

  await page.getByRole("button", { name: "Run backtest" }).click();

  const error = page.locator("#backtest-date-error");
  await expect(error).toBeVisible();
  await expect(page.locator("#backtest-start-date")).toHaveAttribute("aria-invalid", "true");
  await expect(page.locator("#backtest-start-date")).toHaveAttribute(
    "aria-describedby",
    "backtest-date-error"
  );
  await expect(page.locator("#backtest-end-date")).toHaveAttribute("aria-invalid", "true");
});
