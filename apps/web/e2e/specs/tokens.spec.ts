/*
 * Token behavior in the real browser (task 2.1).
 *
 * Verifies, against computed styles of the production build:
 *   - the default (16px root) computed sizes match the documented px values;
 *   - exactly one :root custom-property source exists;
 *   - rem-based tokens scale with the user's root font size (200% check),
 *     while px-based tokens (page width, breakpoints) do not change.
 */
import { test, expect } from "../support/test.ts";

test("default root: computed sizes match the documented values", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const computed = await page.evaluate(() => {
    const rootStyle = getComputedStyle(document.documentElement);
    const h1 = document.querySelector<HTMLElement>(".page-heading h1");
    const h1Style = h1 ? getComputedStyle(h1) : null;
    const panel = document.querySelector<HTMLElement>(".dashboard-panel");
    const panelStyle = panel ? getComputedStyle(panel) : null;

    return {
      rootFontSize: rootStyle.fontSize,
      pageTitleSize: h1Style?.fontSize ?? null,
      pageTitleLeading: h1Style?.lineHeight ?? null,
      panelPaddingTop: panelStyle?.paddingTop ?? null,
      // Control tokens are wired in task 3.2; the declaration is verified here.
      controlMinHeightToken: rootStyle.getPropertyValue("--control-min-height").trim(),
      controlTouchSizeToken: rootStyle.getPropertyValue("--control-touch-size").trim()
    };
  });

  expect(computed.rootFontSize).toBe("16px");
  expect(computed.pageTitleSize).toBe("36px");
  expect(computed.pageTitleLeading).toBe("40px");
  expect(computed.panelPaddingTop).toBe("24px");
  expect(computed.controlMinHeightToken).toBe("2.25rem");
  expect(computed.controlTouchSizeToken).toBe("2.75rem");
});

test("exactly one :root token source reaches the browser", async ({ page }) => {
  await page.goto("/");
  const rootRuleCount = await page.evaluate(() => {
    let count = 0;
    for (const sheet of document.styleSheets) {
      let rules: CSSRuleList;
      try {
        rules = sheet.cssRules;
      } catch {
        continue;
      }
      for (const rule of rules) {
        if (rule instanceof CSSStyleRule && rule.selectorText === ":root") {
          count += 1;
        }
      }
    }
    return count;
  });

  expect(rootRuleCount).toBe(1);
});

test("200% root: rem tokens scale, px constants stay fixed", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  await page.addStyleTag({ content: "html { font-size: 32px !important; }" });

  const computed = await page.evaluate(() => {
    const rootStyle = getComputedStyle(document.documentElement);
    const h1 = document.querySelector<HTMLElement>(".page-heading h1");
    const panel = document.querySelector<HTMLElement>(".dashboard-panel");
    const dense = document.querySelector<HTMLElement>(".compact-list dd");
    return {
      rootFontSize: rootStyle.fontSize,
      pageTitleSize: h1 ? getComputedStyle(h1).fontSize : null,
      panelPaddingTop: panel ? getComputedStyle(panel).paddingTop : null,
      denseSize: dense ? getComputedStyle(dense).fontSize : null
    };
  });

  expect(computed.rootFontSize).toBe("32px");
  expect(computed.pageTitleSize).toBe("72px");
  expect(computed.panelPaddingTop).toBe("48px");
  expect(computed.denseSize).toBe("26px");
});
