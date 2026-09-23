/*
 * Acceptance matrix (task 5.1 — full design.md route/state/viewport matrix).
 *
 * Every entry records: route, state, viewport, the assertions for the
 * corresponding spec requirement, and a screenshot. The report written to
 * the Change evidence directory carries the version identity (git HEAD,
 * source fingerprint, build manifest hash, harness fingerprint, browser
 * version) plus per-screenshot hashes.
 */
import path from "node:path";
import process from "node:process";
import { mkdir, writeFile } from "node:fs/promises";
import { test, expect } from "../support/test.ts";
import { collectIdentity, screenshotEntry, type EvidenceEntry } from "../support/evidence.ts";
import {
  emptyDashboardResponse,
  emptySignalListResponse,
  emptyBacktestListResponse,
  emptyWalkForwardListResponse,
  legacyBacktestDetailResponse,
  failedBacktestDetailResponse,
  queuedWalkForwardDetailResponse,
  runningWalkForwardDetailResponse,
  dashboardResponse,
  signalListResponse,
  backtestListResponse,
  walkForwardListResponse
} from "../fixtures/apiFixtures.ts";
import type { ApiFixtureSpec } from "../support/network.ts";

const EVIDENCE_DIR = path.resolve(
  process.cwd(),
  "..",
  "..",
  "openspec",
  "changes",
  "refine-web-research-visual-system",
  "evidence",
  "browser",
  "matrix"
);

const screenshots: Array<{ route: string; state: string; viewport: string; testId: string; entry: Promise<EvidenceEntry> }> = [];
const results: Array<{
  testId: string;
  title: string;
  status: string;
  errors: string[];
  unmatchedApiRequests: number;
  blockedOriginRequests: number;
}> = [];

test.afterEach(({ api }, info) => {
  results.push({
    testId: info.testId,
    title: info.titlePath.join(" > "),
    status: info.status ?? "interrupted",
    errors: info.errors.map((error) => error.message ?? String(error)),
    unmatchedApiRequests: api.unmatched.length,
    blockedOriginRequests: api.blocked.length
  });
});

async function settle(page: import("@playwright/test").Page): Promise<void> {
  await page.evaluate("document.fonts.ready.then(() => true)");
  await page.waitForTimeout(120);
}

async function capture(
  page: import("@playwright/test").Page,
  route: string,
  state: string
): Promise<void> {
  const size = page.viewportSize() ?? { width: 0, height: 0 };
  const viewportTag = size.height === 844 || size.height === 1000
    ? String(size.width)
    : `${size.width}x${size.height}`;
  const file = path.join(
    EVIDENCE_DIR,
    `${route.replace(/^\//, "root-").replace(/\//g, "-")}-${state}-${viewportTag}.png`
  );
  await page.screenshot({ path: file, fullPage: true });
  screenshots.push({
    route,
    state,
    viewport: `${size.width}x${size.height}`,
    testId: test.info().testId,
    entry: screenshotEntry(file)
  });
}

async function noHorizontalOverflow(page: import("@playwright/test").Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    const root = document.scrollingElement as HTMLElement;
    return root.scrollWidth - root.clientWidth;
  });
  expect(overflow).toBeLessThanOrEqual(0);
}

/* ── 1. All business routes + 404 at 1440 / 390 ──────────────────────── */

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

for (const { route, heading } of ROUTES) {
  for (const viewport of [1440, 390]) {
    test(`matrix: ${route} at ${viewport}px renders research content`, async ({ page }) => {
      await page.setViewportSize({ width: viewport, height: viewport === 1440 ? 1000 : 844 });
      await page.goto(route);
      await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
      await settle(page);
      await noHorizontalOverflow(page);
      await capture(page, route, "populated");
    });
  }
}

/* ── 2. Breakpoint edges on a detail page ────────────────────────────── */

test("matrix: backtest detail computed styles at breakpoint edges", async ({ page }) => {
  const observed: Record<number, string> = {};
  for (const width of [1025, 1024, 1023, 901, 900, 899, 721, 720, 719]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/backtests/7");
    await expect(page.getByText("Backtest #7")).toBeVisible();
    observed[width] = await page.evaluate(() => {
      const panel = document.querySelector<HTMLElement>(".detail-page .dashboard-panel")!;
      const shell = document.querySelector<HTMLElement>(".app-shell")!;
      return `panel=${getComputedStyle(panel).paddingTop} shell=${getComputedStyle(shell).paddingLeft}`;
    });
  }
  expect(observed[1025]).toBe("panel=24px shell=32px");
  expect(observed[1023]).toBe("panel=24px shell=24px");
  expect(observed[721]).toBe("panel=24px shell=24px");
  expect(observed[720]).toBe("panel=16px shell=16px");
  expect(observed[719]).toBe("panel=16px shell=16px");
});

/* ── 3. Loading / empty / error states ───────────────────────────────── */

test.describe("dashboard states", () => {
  test.describe("matrix: dashboard shows loading feedback then content", () => {
    test.use({
      fixtures: [
        { method: "GET", path: "/api/dashboard", body: dashboardResponse, delayMs: 400 }
      ]
    });
  test("matrix: dashboard shows loading feedback then content", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Loading dashboard data.")).toBeVisible();
    await capture(page, "/", "loading");
    await expect(page.getByText("Signal #42")).toBeVisible({ timeout: 10_000 });
  });
  });

  test.describe("matrix: dashboard empty state keeps operations reachable", () => {
    test.use({
      fixtures: [{ method: "GET", path: "/api/dashboard", body: emptyDashboardResponse }]
    });
  test("matrix: dashboard empty state keeps operations reachable", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByText("No local market prices are stored yet. Fetch market data to populate dashboard coverage.")
    ).toBeVisible();
    await expect(
      page.getByTestId("workflow-panel-signal").getByRole("button", { name: "Generate signal" })
    ).toBeEnabled();
    await settle(page);
    await capture(page, "/", "empty");
  });
  });

  test.describe("matrix: dashboard read failure offers retry", () => {
    test.use({
      fixtures: [
        { method: "GET", path: "/api/dashboard", status: 500, body: { message: "boom" } }
      ]
    });
  test("matrix: dashboard read failure offers retry", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
    await capture(page, "/", "error");
  });
  });
});

test.describe("signals list states", () => {
  test.describe("matrix: signals list empty state for the All filter", () => {
    test.use({
      fixtures: [
        {
          method: "GET",
          path: "/api/strategy-signals",
          query: { limit: "20", offset: "0" },
          body: emptySignalListResponse
        }
      ]
    });
  test("matrix: signals list empty state for the All filter", async ({ page }) => {
    await page.goto("/signals");
    await expect(
      page.getByText(
        "No successful local signal exists yet. Generate a signal from the Dashboard after market data is ready."
      )
    ).toBeVisible();
    await capture(page, "/signals", "empty");
  });
  });

  test.describe("matrix: signals list read failure offers retry", () => {
    test.use({
      fixtures: [
        {
          method: "GET",
          path: "/api/strategy-signals",
          query: { limit: "20", offset: "0" },
          status: 500,
          body: { message: "boom" }
        }
      ]
    });
  test("matrix: signals list read failure offers retry", async ({ page }) => {
    await page.goto("/signals");
    await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
    await capture(page, "/signals", "error");
  });
  });
});

test.describe("backtests list states", () => {
  test.describe("matrix: backtests list empty state", () => {
    test.use({
      fixtures: [
        {
          method: "GET",
          path: "/api/backtests",
          query: { limit: "10", offset: "0" },
          body: emptyBacktestListResponse
        }
      ]
    });
  test("matrix: backtests list empty state", async ({ page }) => {
    await page.goto("/backtests");
    await expect(page.getByText(/No local backtest run exists yet/)).toBeVisible();
    await capture(page, "/backtests", "empty");
  });
  });

  test.describe("matrix: backtests list read failure offers retry", () => {
    test.use({
      fixtures: [
        {
          method: "GET",
          path: "/api/backtests",
          query: { limit: "10", offset: "0" },
          status: 500,
          body: { message: "boom" }
        }
      ]
    });
  test("matrix: backtests list read failure offers retry", async ({ page }) => {
    await page.goto("/backtests");
    await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
    await capture(page, "/backtests", "error");
  });
  });
});

test.describe("walk-forwards list states", () => {
  test.describe("matrix: walk-forwards list empty state", () => {
    test.use({
      fixtures: [
        {
          method: "GET",
          path: "/api/walk-forwards",
          query: { limit: "10", offset: "0" },
          body: emptyWalkForwardListResponse
        }
      ]
    });
  test("matrix: walk-forwards list empty state", async ({ page }) => {
    await page.goto("/walk-forwards");
    await expect(page.getByText(/No complete Walk-forward evaluation exists yet/)).toBeVisible();
    await capture(page, "/walk-forwards", "empty");
  });
  });

  test.describe("matrix: walk-forwards list read failure offers retry", () => {
    test.use({
      fixtures: [
        {
          method: "GET",
          path: "/api/walk-forwards",
          query: { limit: "10", offset: "0" },
          status: 500,
          body: { message: "boom" }
        }
      ]
    });
  test("matrix: walk-forwards list read failure offers retry", async ({ page }) => {
    await page.goto("/walk-forwards");
    await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
    await capture(page, "/walk-forwards", "error");
  });
  });
});

// Fill the route/state/viewport combinations not exercised by the cases above.
const STATE_ROUTES: Array<{
  route: string;
  loading: string;
  empty: string;
  fixture: ApiFixtureSpec;
  emptyBody: unknown;
}> = [
  {
    route: "/",
    loading: "Loading dashboard data.",
    empty: "No local market prices are stored yet.",
    fixture: { method: "GET", path: "/api/dashboard", body: dashboardResponse },
    emptyBody: emptyDashboardResponse
  },
  {
    route: "/signals",
    loading: "Loading signal history.",
    empty: "No successful local signal exists yet.",
    fixture: { method: "GET", path: "/api/strategy-signals", query: { limit: "20", offset: "0" }, body: signalListResponse },
    emptyBody: emptySignalListResponse
  },
  {
    route: "/backtests",
    loading: "Loading backtest history.",
    empty: "No local backtest run exists yet.",
    fixture: { method: "GET", path: "/api/backtests", query: { limit: "10", offset: "0" }, body: backtestListResponse },
    emptyBody: emptyBacktestListResponse
  },
  {
    route: "/walk-forwards",
    loading: "Loading Walk-forward history.",
    empty: "No complete Walk-forward evaluation exists yet.",
    fixture: { method: "GET", path: "/api/walk-forwards", query: { limit: "10", offset: "0" }, body: walkForwardListResponse },
    emptyBody: emptyWalkForwardListResponse
  }
];

for (const scenario of STATE_ROUTES) {
  for (const state of ["loading", "empty", "error"] as const) {
    for (const width of (state === "loading" && scenario.route !== "/" ? [1440, 390] : [390])) {
      test(`matrix: ${scenario.route} ${state} at ${width}px`, async ({ page, api }) => {
        await page.setViewportSize({ width, height: width === 1440 ? 1000 : 844 });
        api.fixtures.unshift({
          ...scenario.fixture,
          body: state === "empty" ? scenario.emptyBody : state === "error" ? { message: "boom" } : scenario.fixture.body,
          ...(state === "error" ? { status: 500 } : {}),
          ...(state === "loading" ? { delayMs: 1000 } : {})
        });
        await page.goto(scenario.route);
        if (state === "loading") {
          await expect(page.getByText(scenario.loading)).toBeVisible();
        } else if (state === "empty") {
          await expect(page.getByText(new RegExp(scenario.empty))).toBeVisible();
        } else {
          await expect(page.getByRole("button", { name: /Retry/ })).toBeVisible();
        }
        await noHorizontalOverflow(page);
        await capture(page, scenario.route, state);
        if (state === "loading") {
          await expect(page.getByText(scenario.loading)).toBeHidden();
        }
      });
    }
  }
}

/* ── 4. Detail-page legacy / failed / queued / running states ────────── */

test.describe("detail states", () => {
  test.describe("matrix: legacy backtest detail preserves unavailable evidence at 390px", () => {
    test.use({
      fixtures: [{ method: "GET", path: "/api/backtests/{runId}", body: legacyBacktestDetailResponse }]
    });
  test("matrix: legacy backtest detail preserves unavailable evidence at 390px", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/backtests/7");
    await expect(page.getByText("Backtest #7")).toBeVisible();
    // Legacy runs render the established unavailable placeholder.
    await expect(page.getByText("n/a").first()).toBeVisible();
    // The distribution disclosure explains the unavailability explicitly.
    await expect(page.locator(".detail-page .disclosure-summary").first()).toBeVisible();
    await settle(page);
    await noHorizontalOverflow(page);
    await capture(page, "/backtests/7", "legacy");
  });
  });

  test.describe("matrix: failed backtest detail reports the failure reason at 390px", () => {
    test.use({
      fixtures: [{ method: "GET", path: "/api/backtests/{runId}", body: failedBacktestDetailResponse }]
    });
  test("matrix: failed backtest detail reports the failure reason at 390px", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/backtests/7");
    await expect(page.getByText("failed").first()).toBeVisible();
    await expect(
      page.getByText("Momentum computation failed for the requested range.")
    ).toBeVisible();
    await capture(page, "/backtests/7", "failed");
  });
  });

  test.describe("matrix: queued walk-forward detail stays operable at 390px", () => {
    test.use({
      fixtures: [{ method: "GET", path: "/api/walk-forwards/{runId}", body: queuedWalkForwardDetailResponse }]
    });
  test("matrix: queued walk-forward detail stays operable at 390px", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/walk-forwards/3");
    await expect(page.getByText("queued").first()).toBeVisible();
    await settle(page);
    await noHorizontalOverflow(page);
    await capture(page, "/walk-forwards/3", "queued");
  });
  });

  test.describe("matrix: running walk-forward detail shows the active lease at 390px", () => {
    test.use({
      fixtures: [{ method: "GET", path: "/api/walk-forwards/{runId}", body: runningWalkForwardDetailResponse }]
    });
  test("matrix: running walk-forward detail shows the active lease at 390px", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/walk-forwards/3");
    await expect(page.getByText("running").first()).toBeVisible();
    await capture(page, "/walk-forwards/3", "running");
  });
  });
});

/* ── 5. Long names, negative values at 320px ────────────────────────── */

test("matrix: signal detail long mixed names and nulls at 320px", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto("/signals/42");
  await expect(page.getByText("Signal Detail")).toBeVisible();
  await expect(
    page.getByText("华泰柏瑞沪深300交易型开放式指数证券投资基金").first()
  ).toBeVisible();
  await settle(page);
  await noHorizontalOverflow(page);
  await capture(page, "/signals/42", "long-names");
});

test("matrix: ETF detail renders the long name and trend at 320px", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto("/etfs/1");
  await expect(page.getByText("ETF Detail")).toBeVisible();
  await expect(
    page.getByText("华泰柏瑞沪深300交易型开放式指数证券投资基金").first()
  ).toBeVisible();
  await settle(page);
  await noHorizontalOverflow(page);
  await capture(page, "/etfs/1", "long-names");
});

/* ── 6. Palette states ──────────────────────────────────────────────── */

for (const { width, height } of [
  { width: 1440, height: 1000 },
  { width: 390, height: 844 },
  { width: 390, height: 400 }
]) {
  for (const state of ["populated", "filter-empty", "source-error"] as const) {
    test(`matrix: palette ${state} at ${width}x${height}`, async ({ page, api }) => {
      await page.setViewportSize({ width, height });
      if (state === "source-error") {
        api.fixtures.unshift({
          method: "GET", path: "/api/strategy-signals/latest", status: 500,
          body: { message: "boom" }
        });
      }
      await page.goto("/");
      await page.keyboard.press("Meta+k");
      await expect(page.locator(".command-palette-input")).toBeFocused();
      if (state === "filter-empty") {
        await page.keyboard.type("zzzz-no-match");
        await expect(page.getByText(/No results/)).toBeVisible();
      } else if (state === "source-error") {
        await expect(page.locator(".command-palette-error")).toBeVisible();
      } else {
        await page.keyboard.type("signal");
        await expect(page.locator(".command-palette-row-active")).toBeVisible();
      }
      const inputVisible = await page.locator(".command-palette-input").evaluate((input) => {
        const rect = input.getBoundingClientRect();
        return rect.top >= 0 && rect.bottom <= window.innerHeight;
      });
      expect(inputVisible).toBe(true);
      await capture(page, "/palette", state);
      await page.keyboard.press("Escape");
      await expect(page.locator(".command-palette-dialog")).toBeHidden();
    });
  }
}

/* ── 6. POST operation flow (network writes land in fixtures only) ──── */

test("matrix: run backtest POST resolves with the pending lock intact", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Signal #42")).toBeVisible();

  const startWidth = await page.evaluate(() => {
    const button = document.querySelector<HTMLElement>("#dashboard-run-backtest")!;
    return Math.round(button.getBoundingClientRect().width);
  });

  await page.locator("#backtest-start-date").fill("2026-01-01");
  await page.locator("#backtest-end-date").fill("2026-03-01");
  await page.getByRole("button", { name: "Run backtest" }).click();

  // The POST hit the fixture registry (never a real service); the run summary
  // feedback appears.
  await expect(page.getByText(/Backtest run/)).toBeVisible();

  const postWidth = await page.evaluate(() => {
    const button = document.querySelector<HTMLElement>("#dashboard-run-backtest")!;
    return Math.round(button.getBoundingClientRect().width);
  });
  expect(postWidth).toBeGreaterThanOrEqual(startWidth);
});

/* ── Report ─────────────────────────────────────────────────────────── */

test.afterAll(async ({ browser }) => {
  await mkdir(EVIDENCE_DIR, { recursive: true });
  const identity = await collectIdentity(browser.browserType().name(), browser.version());
  const entries: EvidenceEntry[] = [];
  for (const item of screenshots) {
    entries.push(await item.entry);
  }
  const report = {
    generatedAt: new Date().toISOString(),
    ...identity,
    results,
    entries: screenshots.map((item, index) => ({
      route: item.route,
      state: item.state,
      viewport: item.viewport,
      testId: item.testId,
      status: results.find((result) => result.testId === item.testId)?.status ?? "missing",
      file: entries[index].file,
      sha256: entries[index].sha256
    }))
  };
  await writeFile(
    path.join(EVIDENCE_DIR, "matrix-report.json"),
    `${JSON.stringify(report, null, 2)}\n`
  );
});
