/*
 * Isolation verification (task 1.3).
 *
 * Verifies the fail-closed network guard with deliberately unmatched
 * requests:
 *   - an unmatched `/api` request is intercepted first (never reaches the
 *     network) and is recorded as unmatched;
 *   - a request to another local origin (127.0.0.1:8000, the real backend
 *     port) is blocked before leaving the browser;
 *   - a POST never reaches a real API;
 *   - no service worker can be registered to bypass interception.
 * The two probes are declared as expected in the registry so the run-level
 * guard treats exactly them as verified-blocking probes; any other stray
 * request still fails the run.
 */
import { test, expect } from "../support/test";

test("an unmatched /api request is blocked, recorded, and fails closed", async ({
  page,
  api
}) => {
  api.declareUnmatched("GET", "/api/__probe_unmatched__");
  await page.goto("/");

  const outcome = await page.evaluate(async () => {
    try {
      const response = await fetch("/api/__probe_unmatched__");
      return { reached: true, status: response.status };
    } catch {
      return { reached: false };
    }
  });

  expect(outcome.reached, "unmatched /api request must not be fulfilled").toBe(false);
  expect(api.unmatched).toHaveLength(1);
  expect(api.unmatched[0].pathname).toBe("/api/__probe_unmatched__");
  expect(api.match("GET", new URL("http://127.0.0.1:4174/api/__probe_unmatched__"))).toBeNull();
});

test("a cross-origin request to another local port is blocked", async ({ page, api }) => {
  api.declareBlocked("GET", "http://127.0.0.1:8000/api/health");
  await page.goto("/");

  const outcome = await page.evaluate(async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/health");
      return { reached: true, status: response.status };
    } catch {
      return { reached: false };
    }
  });

  expect(outcome.reached, "cross-origin request must be blocked").toBe(false);
  expect(api.blocked).toHaveLength(1);
  expect(api.blocked[0].method).toBe("GET");
  expect(new URL(api.blocked[0].url).port).toBe("8000");
});

test("an unmatched POST never reaches a real API", async ({ page, api }) => {
  api.declareUnmatched("POST", "/api/__probe_unmatched_post__");
  await page.goto("/");

  const outcome = await page.evaluate(async () => {
    try {
      const response = await fetch("/api/__probe_unmatched_post__", { method: "POST" });
      return { reached: true, status: response.status };
    } catch {
      return { reached: false };
    }
  });

  expect(outcome.reached, "POST without fixture must be aborted").toBe(false);
  expect(api.unmatched).toHaveLength(1);
  expect(api.unmatched[0].method).toBe("POST");
});

test("service workers cannot register and bypass interception", async ({ page }) => {
  await page.goto("/");

  const swState = await page.evaluate(() => {
    // The init script removed navigator.serviceWorker; read it defensively so
    // this compiles without DOM lib types.
    const nav = navigator as unknown as { serviceWorker?: { register?: unknown } };
    return {
      serviceWorker: typeof nav.serviceWorker,
      registerAvailable: typeof nav.serviceWorker?.register
    };
  });

  // The init script removed navigator.serviceWorker entirely.
  expect(swState.serviceWorker).toBe("undefined");
  expect(swState.registerAvailable).toBe("undefined");
});
