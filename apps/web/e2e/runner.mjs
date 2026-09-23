/*
 * e2e/runner.mjs — acceptance runner for the visual-system browser workflow.
 *
 * Responsibilities (per the `web-frontend-app` capability requirement
 * "Visual acceptance is reproducible and isolated from persistent data"):
 *   1. Refuse to run when VITE_API_BASE_URL is set, so the acceptance build
 *      always uses the relative `/api` base URL.
 *   2. Produce the production build (`vite build`, writes `dist/`).
 *   3. Serve `dist/` on a dedicated port with NO `/api` proxy (the preview
 *      server would otherwise inherit the dev `server.proxy` rule that
 *      forwards `/api` to `127.0.0.1:8000`).
 *   4. Start and stop the server inside the runner; no FastAPI backend is
 *      started and no default database is touched.
 */
import { build, preview } from "vite";
import { fileURLToPath } from "node:url";
import path from "node:path";
import process from "node:process";
import console from "node:console";
import { setTimeout } from "node:timers";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

if (process.env.VITE_API_BASE_URL !== undefined && process.env.VITE_API_BASE_URL !== "") {
  console.error(
    "[e2e] VITE_API_BASE_URL is set — unset it so the acceptance build uses the relative /api base URL."
  );
  process.exit(1);
}

const port = Number(process.env.VELA_E2E_PORT ?? 4174);

console.log(`[e2e] Building production bundle (root: ${webRoot})...`);
await build({ root: webRoot, mode: "production", logLevel: "warn" });

console.log(`[e2e] Starting static preview server on port ${port} (proxy disabled)...`);
const server = await preview({
  root: webRoot,
  preview: {
    // Bind IPv4 loopback explicitly so the Playwright baseURL (127.0.0.1)
    // reaches the server (vite's default host resolves to [::1] here).
    host: "127.0.0.1",
    port,
    strictPort: true,
    // Explicitly disable the proxy so `/api` requests reach this process's
    // route interception instead of a real backend.
    proxy: {}
  }
});

function shutdown(signal) {
  console.log(`[e2e] ${signal} received; closing preview server.`);
  server.httpServer.close(() => process.exit(0));
  // Force-exit if close hangs.
  setTimeout(() => process.exit(0), 2000).unref();
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

console.log(`[e2e] Ready: http://127.0.0.1:${port}`);
