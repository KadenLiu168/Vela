/*
 * Pre-change visual baseline (task 1.4).
 *
 * Captures Dashboard and Backtest Detail at 1440x1000 and 390x844 BEFORE any
 * visual change, together with the version identity (git HEAD, source
 * fingerprint, build manifest hash, fixtures/harness fingerprint, browser
 * version) and per-screenshot sha256. The report verifies its referenced
 * artifacts exist. Run via `npm run test:e2e:baseline`.
 */
import path from "node:path";
import process from "node:process";
import { test, expect } from "../support/test.ts";
import {
  collectIdentity,
  screenshotEntry,
  writeEvidenceReport,
  type EvidenceReport
} from "../support/evidence.ts";

const CHANGE_EVIDENCE_DIR = path.resolve(
  process.cwd(),
  "..",
  "..",
  "openspec",
  "changes",
  "refine-web-research-visual-system",
  "evidence",
  "browser",
  "baseline"
);

test.skip(
  process.env.VELA_E2E_BASELINE !== "1",
  "baseline capture runs only via test:e2e:baseline"
);

const VIEWPORTS = [
  { name: "1440", width: 1440, height: 1000 },
  { name: "390", width: 390, height: 844 }
];

async function settle(page: import("@playwright/test").Page): Promise<void> {
  // String expression: evaluated in the browser context without DOM lib types.
  await page.evaluate("document.fonts.ready.then(() => true)");
  await page.waitForTimeout(150);
}

for (const viewport of VIEWPORTS) {
  test(`baseline: Dashboard at ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/");
    await expect(page.getByText("Signal #42")).toBeVisible();
    await settle(page);
    const file = path.join(CHANGE_EVIDENCE_DIR, `dashboard-${viewport.name}.png`);
    await page.screenshot({ path: file, fullPage: true });
  });

  test(`baseline: Backtest Detail at ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto("/backtests/7");
    await expect(page.getByText("Backtest #7")).toBeVisible();
    await expect(page.getByRole("list", { name: "Equity curve legend" })).toBeVisible();
    await settle(page);
    const file = path.join(CHANGE_EVIDENCE_DIR, `backtest-detail-${viewport.name}.png`);
    await page.screenshot({ path: file, fullPage: true });
  });
}

test.afterAll(async ({ browser }) => {
  if (process.env.VELA_E2E_BASELINE !== "1") {
    return;
  }
  const identity = await collectIdentity(browser.browserType().name(), browser.version());
  const screenshots = [];
  for (const viewport of VIEWPORTS) {
    for (const routeName of ["dashboard", "backtest-detail"]) {
      screenshots.push(await screenshotEntry(path.join(CHANGE_EVIDENCE_DIR, `${routeName}-${viewport.name}.png`)));
    }
  }
  const report: EvidenceReport = {
    generatedAt: new Date().toISOString(),
    ...identity,
    screenshots
  };
  await writeEvidenceReport(CHANGE_EVIDENCE_DIR, report);
});
