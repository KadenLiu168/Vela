/*
 * Playwright configuration for the Vela web acceptance workflow.
 *
 * The web server is `e2e/runner.mjs`, which:
 *   - refuses to run when VITE_API_BASE_URL is set,
 *   - produces the production build with the relative `/api` base URL,
 *   - serves `dist/` with the `/api` proxy disabled.
 * Playwright starts and stops it; nothing else runs. Reuse of an existing
 * server is disabled so evidence is always tied to the current build.
 */
import { defineConfig } from "@playwright/test";

const port = Number(process.env.VELA_E2E_PORT ?? 4174);

export default defineConfig({
  testDir: "./e2e/specs",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "../build/e2e-report" }],
    ["./e2e/support/evidenceReporter.mjs"]
  ],
  outputDir: "../build/e2e-artifacts",
  webServer: {
    command: "node e2e/runner.mjs",
    port,
    reuseExistingServer: false,
    timeout: 180_000
  },
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    serviceWorkers: "block",
    actionTimeout: 5_000,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    viewport: { width: 1440, height: 1000 }
  }
});
