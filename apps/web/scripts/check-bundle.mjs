import { readdir, readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import { analyzeManifest } from "./bundle-manifest.mjs";

const appRoot = dirname(fileURLToPath(import.meta.url));
const outputDirectory = join(appRoot, "..", "dist");
const manifest = JSON.parse(await readFile(join(outputDirectory, ".vite", "manifest.json"), "utf8"));
const report = await analyzeManifest({ manifest, outputDirectory });
const expectedRouteSources = [
  "BacktestDetailPage.tsx",
  "BacktestListPage.tsx",
  "EtfDetailPage.tsx",
  "SignalDetailPage.tsx",
  "SignalListPage.tsx"
];
const dynamicRouteEntries = expectedRouteSources.map((source) => {
  const entry = report.dynamicEntries.find((candidate) => candidate.source.endsWith(source));
  if (!entry) throw new Error(`Missing dynamic route entry for ${source}.`);
  return entry;
});
const html = await readFile(join(outputDirectory, "index.html"), "utf8");

if (report.initial.rawBytes > 232000) {
  throw new Error(`Dashboard initial JavaScript is ${report.initial.rawBytes} bytes, above the 232000-byte budget.`);
}
if (report.initial.gzipBytes > 72000) {
  throw new Error(`Dashboard initial gzip JavaScript is ${report.initial.gzipBytes} bytes, above the 72000-byte budget.`);
}
if (report.totalJavaScript.rawBytes > 259541) {
  throw new Error(`Total JavaScript is ${report.totalJavaScript.rawBytes} bytes, above the 259541-byte budget.`);
}

const initialFileSet = new Set(report.initial.files);
for (const entry of dynamicRouteEntries) {
  if (initialFileSet.has(entry.file)) {
    throw new Error(`${entry.source} is incorrectly included in the Dashboard static graph.`);
  }
  if (html.includes(entry.file)) {
    throw new Error(`${entry.source} is incorrectly module-preloaded by the Dashboard HTML.`);
  }
}

const reactVendor = report.initial.files.find((file) => /(^|\/)react-vendor-[^/]+\.js$/.test(file));
if (!reactVendor) {
  throw new Error("Dashboard static graph does not include the react-vendor chunk.");
}

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
  css: await measureAssets(outputDirectory, ".css"),
  dynamicRouteEntries,
  fonts: await measureAssets(outputDirectory, ".woff2"),
  initialJavaScript: report.initial,
  reactVendor,
  totalJavaScript: report.totalJavaScript
}, null, 2));
