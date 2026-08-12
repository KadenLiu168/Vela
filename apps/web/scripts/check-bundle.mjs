import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFile, readdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import { analyzeManifest, evaluateBudgets } from "./bundle-manifest.mjs";
import { measureIsolatedRuntime } from "./runtime-baseline.mjs";

const appRoot = dirname(fileURLToPath(import.meta.url));
const webRoot = join(appRoot, "..");
const outputDirectory = join(webRoot, "dist");
const reviewedIdentity = {
  node: "v25.8.2",
  npm: "11.11.1",
  vite: "7.3.6",
  lockfile: "770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34"
};
const budgets = {
  requiredRuntimeRaw: 229187,
  requiredRuntimeGzip: 73544,
  eagerApplicationRaw: 40000,
  eagerApplicationGzip: 12000,
  // Lazy-route allocation raised for `redesign-backtest-results-ui`:
  // BacktestDetailPage now carries the hero, comparison matrix, and chart
  // enhancements (measured 68062 raw bytes on the 2026-08-12 fresh build).
  lazyRouteRaw: 70000,
  initialRaw: 273000,
  initialGzip: 86000,
  // Total-JavaScript budget raised for the same change (measured 337206 raw
  // bytes on the 2026-08-12 fresh build).
  totalRaw: 340000
};
const reviewedRuntimeComponents = {
  reactVendor: { rawBytes: 192347, gzipBytes: 60212 },
  router: { rawBytes: 36840, gzipBytes: 13332 }
};

execFileSync("npm", ["run", "build"], { cwd: webRoot, stdio: "inherit" });

const [manifestText, vitePackageText, lockfileText] = await Promise.all([
  readFile(join(outputDirectory, ".vite", "manifest.json"), "utf8"),
  readFile(join(webRoot, "node_modules", "vite", "package.json"), "utf8"),
  readFile(join(webRoot, "package-lock.json"), "utf8")
]);
const manifest = JSON.parse(manifestText);
const identity = {
  node: process.version,
  npm: execFileSync("npm", ["--version"], { encoding: "utf8" }).trim(),
  vite: JSON.parse(vitePackageText).version,
  lockfile: createHash("sha256").update(lockfileText).digest("hex")
};
const runtimeMeasurement = await measureIsolatedRuntime(webRoot);

const report = await analyzeManifest({
  manifest,
  outputDirectory,
  identity,
  runtimeMeasurement,
  requiredRuntime: {
    rawBytes: budgets.requiredRuntimeRaw,
    gzipBytes: budgets.requiredRuntimeGzip
  }
});
const expectedRouteSources = [
  "SignalListPage.tsx",
  "SignalDetailPage.tsx",
  "BacktestListPage.tsx",
  "BacktestDetailPage.tsx",
  "EtfDetailPage.tsx",
  "WalkForwardListPage.tsx",
  "WalkForwardDetailPage.tsx"
];
const dynamicRouteEntries = expectedRouteSources.map((source) => {
  return report.dynamicEntries.find((candidate) => candidate.source === `src/pages/${source}`);
}).filter(Boolean);
const html = await readFile(join(outputDirectory, "index.html"), "utf8");
const violations = evaluateBudgets({
  report,
  budgets,
  expectedRouteSources,
  html,
  reviewedIdentity,
  reviewedRuntimeComponents
});

async function measureAssets(directory, extension) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) return measureAssets(path, extension);
      if (!entry.name.endsWith(extension)) return { gzipBytes: 0, rawBytes: 0 };
      const contents = await readFile(path);
      return { gzipBytes: gzipSync(contents).length, rawBytes: contents.length };
    })
  );
  return nested.reduce(
    (total, measurement) => ({
      gzipBytes: total.gzipBytes + measurement.gzipBytes,
      rawBytes: total.rawBytes + measurement.rawBytes
    }),
    { gzipBytes: 0, rawBytes: 0 }
  );
}

console.log(JSON.stringify({
  buildIdentity: identity,
  budgets,
  css: await measureAssets(outputDirectory, ".css"),
  dynamicRouteEntries,
  fonts: await measureAssets(outputDirectory, ".woff2"),
  eagerApplication: report.eagerApplication,
  initialJavaScript: report.initial,
  lazyJavaScript: report.lazyJavaScript,
  requiredRuntime: report.requiredRuntime,
  runtimeMeasurement: report.runtimeMeasurement,
  reviewedRuntimeComponents,
  reactVendor: report.initial.files.find((file) => /(^|\/)react-vendor-[^/]+\.js$/.test(file)),
  totalJavaScript: report.totalJavaScript,
  violations
}, null, 2));

if (violations.length > 0) {
  process.exit(1);
}
