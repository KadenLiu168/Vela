import { gzipSync } from "node:zlib";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, expect, it } from "vitest";
import { analyzeManifest, evaluateBudgets } from "./bundle-manifest.mjs";

const temporaryDirectories = [];

afterEach(async () => {
  await Promise.all(temporaryDirectories.splice(0).map((directory) => rm(directory, { force: true, recursive: true })));
});

it("separates dynamic entries from the recursive initial graph and measures individual gzip sizes", async () => {
  const outputDirectory = await mkdtemp(join(tmpdir(), "vela-bundle-manifest-"));
  temporaryDirectories.push(outputDirectory);

  const files = {
    "assets/entry.js": "entry",
    "assets/react-vendor.js": "react vendor runtime",
    "assets/signals.js": "signals route"
  };
  await mkdir(join(outputDirectory, "assets"));
  await Promise.all(
    Object.entries(files).map(([file, contents]) => writeFile(join(outputDirectory, file), contents))
  );

  const result = await analyzeManifest({
    manifest: {
      "index.html": {
        file: "assets/entry.js",
        imports: ["_react-vendor.js"],
        isEntry: true,
        dynamicImports: ["src/pages/SignalListPage.tsx"]
      },
      "_react-vendor.js": { file: "assets/react-vendor.js" },
      "src/pages/SignalListPage.tsx": {
        file: "assets/signals.js",
        isDynamicEntry: true,
        src: "src/pages/SignalListPage.tsx"
      }
    },
    outputDirectory
  });

  expect(result.initial.files).toEqual(["assets/entry.js", "assets/react-vendor.js"]);
  expect(result.dynamicEntries).toEqual([
    { file: "assets/signals.js", source: "src/pages/SignalListPage.tsx" }
  ]);
  expect(result.initial.rawBytes).toBe(Buffer.byteLength(files["assets/entry.js"]) + Buffer.byteLength(files["assets/react-vendor.js"]));
  expect(result.initial.gzipBytes).toBe(gzipSync(files["assets/entry.js"]).length + gzipSync(files["assets/react-vendor.js"]).length);
  expect(result.totalJavaScript.rawBytes).toBe(
    Object.values(files).reduce((total, contents) => total + Buffer.byteLength(contents), 0)
  );
});

it("records clean-build identity fields in the analysis report", async () => {
  const outputDirectory = await mkdtemp(join(tmpdir(), "vela-bundle-identity-"));
  temporaryDirectories.push(outputDirectory);
  await mkdir(join(outputDirectory, "assets"));
  await writeFile(join(outputDirectory, "assets/entry.js"), "entry");

  const identity = { node: "v22.0.0", npm: "10.0.0", vite: "7.0.0", lockfile: "abc123" };
  const result = await analyzeManifest({
    manifest: {
      "index.html": { file: "assets/entry.js", isEntry: true }
    },
    outputDirectory,
    identity
  });

  expect(result.identity).toEqual(identity);
});

it("traverses nested static imports recursively and keeps dynamic-entry chains out of the initial graph", async () => {
  const outputDirectory = await mkdtemp(join(tmpdir(), "vela-bundle-traversal-"));
  temporaryDirectories.push(outputDirectory);
  await mkdir(join(outputDirectory, "assets"));
  const files = {
    "assets/entry.js": "entry",
    "assets/vendor.js": "vendor",
    "assets/shared.js": "shared",
    "assets/nested.js": "nested",
    "assets/dynamic.js": "dynamic route",
    "assets/dynamic-shared.js": "dynamic-only shared"
  };
  await Promise.all(
    Object.entries(files).map(([file, contents]) => writeFile(join(outputDirectory, file), contents))
  );

  const result = await analyzeManifest({
    manifest: {
      "index.html": {
        file: "assets/entry.js",
        imports: ["_vendor.js"],
        isEntry: true,
        dynamicImports: ["src/pages/BacktestListPage.tsx"]
      },
      "_vendor.js": { file: "assets/vendor.js", imports: ["_shared.js"] },
      "_shared.js": { file: "assets/shared.js", imports: ["_nested.js"] },
      "_nested.js": { file: "assets/nested.js" },
      "src/pages/BacktestListPage.tsx": {
        file: "assets/dynamic.js",
        imports: ["_dynamic-shared.js"],
        isDynamicEntry: true,
        src: "src/pages/BacktestListPage.tsx"
      },
      "_dynamic-shared.js": { file: "assets/dynamic-shared.js" }
    },
    outputDirectory
  });

  expect(result.initial.files).toEqual(["assets/entry.js", "assets/vendor.js", "assets/shared.js", "assets/nested.js"]);
  expect(result.initial.files).not.toContain("assets/dynamic.js");
  expect(result.initial.files).not.toContain("assets/dynamic-shared.js");
  expect(result.totalJavaScript.files).toContain("assets/dynamic.js");
  expect(result.totalJavaScript.files).toContain("assets/dynamic-shared.js");
  expect(result.totalJavaScript.rawBytes).toBe(
    Object.values(files).reduce((total, contents) => total + Buffer.byteLength(contents), 0)
  );
});

const EXPECTED_ROUTE_SOURCES = [
  "SignalListPage.tsx",
  "SignalDetailPage.tsx",
  "BacktestListPage.tsx",
  "BacktestDetailPage.tsx",
  "EtfDetailPage.tsx",
  "WalkForwardListPage.tsx",
  "WalkForwardDetailPage.tsx"
];

const BUDGETS = { initialRaw: 232000, initialGzip: 72000, totalRaw: 259541 };

const REVIEWED_IDENTITY = {
  node: "v25.8.2",
  npm: "11.11.1",
  vite: "7.3.6",
  lockfile: "770031e7e424b525f90d9da3ea5b7fea06e2e9e67d61b819e9cf50102cd77a34"
};

const REVISED_BUDGETS = {
  requiredRuntimeRaw: 229187,
  requiredRuntimeGzip: 73544,
  eagerApplicationRaw: 40000,
  eagerApplicationGzip: 12000,
  lazyRouteRaw: 61000,
  initialRaw: 273000,
  initialGzip: 86000,
  totalRaw: 333000
};

const REVIEWED_RUNTIME_COMPONENTS = {
  reactVendor: { rawBytes: 192347, gzipBytes: 60212 },
  router: { rawBytes: 36840, gzipBytes: 13332 }
};

it("aggregates every violated budget and ownership condition without early exit", async () => {
  const report = {
    dynamicEntries: [],
    initial: { files: ["assets/entry.js"], rawBytes: 300000, gzipBytes: 100000 },
    totalJavaScript: { files: ["assets/entry.js"], rawBytes: 400000 }
  };

  const violations = evaluateBudgets({ report, budgets: BUDGETS, expectedRouteSources: EXPECTED_ROUTE_SOURCES, html: "<html></html>" });

  expect(violations).toContain("Dashboard initial JavaScript is 300000 bytes, above the 232000-byte budget.");
  expect(violations).toContain("Dashboard initial gzip JavaScript is 100000 bytes, above the 72000-byte budget.");
  expect(violations).toContain("Total JavaScript is 400000 bytes, above the 259541-byte budget.");
  for (const source of EXPECTED_ROUTE_SOURCES) {
    expect(violations).toContain(`Missing dynamic route entry for ${source}.`);
  }
  expect(violations).toContain("Dashboard static graph does not include the react-vendor chunk.");
});

it("rejects lazy-route ownership by the initial graph or Dashboard module-preload markup", async () => {
  const report = {
    dynamicEntries: EXPECTED_ROUTE_SOURCES.map((source) => ({ file: `assets/${source}.js`, source: `src/pages/${source}` })),
    initial: {
      files: ["assets/entry.js", "assets/WalkForwardListPage.tsx.js", "assets/WalkForwardDetailPage.tsx.js"],
      rawBytes: 1000,
      gzipBytes: 500
    },
    totalJavaScript: { files: ["assets/entry.js"], rawBytes: 1000 }
  };
  const html = '<script type="module" crossorigin src="/assets/SignalListPage.tsx.js"></script>';

  const violations = evaluateBudgets({ report, budgets: BUDGETS, expectedRouteSources: EXPECTED_ROUTE_SOURCES, html });

  expect(violations).toContain("WalkForwardListPage.tsx is incorrectly included in the Dashboard static graph.");
  expect(violations).toContain("WalkForwardDetailPage.tsx is incorrectly included in the Dashboard static graph.");
  expect(violations).toContain("SignalListPage.tsx is incorrectly module-preloaded by the Dashboard HTML.");
  expect(violations.filter((violation) => violation.startsWith("Missing dynamic route entry"))).toHaveLength(0);
});

it("attributes required runtime, eager application, and non-initial lazy JavaScript", async () => {
  const outputDirectory = await mkdtemp(join(tmpdir(), "vela-bundle-attribution-"));
  temporaryDirectories.push(outputDirectory);
  await mkdir(join(outputDirectory, "assets"));
  const files = {
    "assets/entry.js": "entry",
    "assets/react-vendor.js": "react vendor runtime",
    "assets/route.js": "lazy route",
    "assets/lazy-shared.js": "lazy shared"
  };
  await Promise.all(
    Object.entries(files).map(([file, contents]) => writeFile(join(outputDirectory, file), contents))
  );

  const requiredRuntime = { rawBytes: 229187, gzipBytes: 73544 };
  const report = await analyzeManifest({
    manifest: {
      "index.html": {
        file: "assets/entry.js",
        imports: ["_react-vendor.js"],
        isEntry: true,
        dynamicImports: ["src/pages/SignalListPage.tsx"]
      },
      "_react-vendor.js": { file: "assets/react-vendor.js" },
      "src/pages/SignalListPage.tsx": {
        file: "assets/route.js",
        imports: ["_lazy-shared.js"],
        isDynamicEntry: true,
        src: "src/pages/SignalListPage.tsx"
      },
      "_lazy-shared.js": { file: "assets/lazy-shared.js" }
    },
    outputDirectory,
    identity: REVIEWED_IDENTITY,
    requiredRuntime
  });

  expect(report.requiredRuntime).toEqual(requiredRuntime);
  expect(report.eagerApplication.rawBytes).toBe(report.initial.rawBytes - requiredRuntime.rawBytes);
  expect(report.eagerApplication.gzipBytes).toBe(report.initial.gzipBytes - requiredRuntime.gzipBytes);
  expect(report.lazyJavaScript.files).toEqual(["assets/route.js", "assets/lazy-shared.js"]);
  expect(report.lazyJavaScript.rawBytes).toBe(report.totalJavaScript.rawBytes - report.initial.rawBytes);
});

it("reports identity, runtime, allocation, revised-budget, and ownership violations together", () => {
  const report = {
    dynamicEntries: [],
    identity: { ...REVIEWED_IDENTITY, vite: "7.3.7" },
    runtimeMeasurement: {
      reactVendor: { rawBytes: 192347, gzipBytes: 60212 },
      router: { rawBytes: 36840, gzipBytes: 13332 }
    },
    requiredRuntime: { rawBytes: 229188, gzipBytes: 73545 },
    eagerApplication: { rawBytes: 40001, gzipBytes: 12001 },
    lazyJavaScript: { rawBytes: 61001, gzipBytes: 0 },
    initial: { files: ["assets/entry.js"], rawBytes: 273001, gzipBytes: 86001 },
    totalJavaScript: { files: ["assets/entry.js"], rawBytes: 333001 }
  };

  const violations = evaluateBudgets({
    report,
    budgets: REVISED_BUDGETS,
    expectedRouteSources: EXPECTED_ROUTE_SOURCES,
    html: "<html></html>",
    reviewedIdentity: REVIEWED_IDENTITY,
    reviewedRuntimeComponents: REVIEWED_RUNTIME_COMPONENTS
  });

  expect(violations).toContain("Build identity does not match the reviewed identity.");
  expect(violations).toContain("Required runtime raw JavaScript is 229188 bytes, above the 229187-byte baseline.");
  expect(violations).toContain("Required runtime gzip JavaScript is 73545 bytes, above the 73544-byte baseline.");
  expect(violations).toContain("Eager application raw JavaScript is 40001 bytes, above the 40000-byte allocation.");
  expect(violations).toContain("Eager application gzip JavaScript is 12001 bytes, above the 12000-byte allocation.");
  expect(violations).toContain("Lazy-route JavaScript is 61001 bytes, above the 61000-byte allocation.");
  expect(violations).toContain("Dashboard initial JavaScript is 273001 bytes, above the 273000-byte budget.");
  expect(violations).toContain("Dashboard initial gzip JavaScript is 86001 bytes, above the 86000-byte budget.");
  expect(violations).toContain("Total JavaScript is 333001 bytes, above the 333000-byte budget.");
  expect(violations).toContain("Dashboard static graph does not include the react-vendor chunk.");
  expect(violations.filter((violation) => violation.startsWith("Missing dynamic route entry"))).toHaveLength(7);
});

it("accepts the reviewed identity and all revised budget bands", () => {
  const report = {
    dynamicEntries: EXPECTED_ROUTE_SOURCES.map((source) => ({
      file: `assets/${source}.js`,
      source: `src/pages/${source}`
    })),
    identity: REVIEWED_IDENTITY,
    runtimeMeasurement: {
      reactVendor: { rawBytes: 192347, gzipBytes: 60212 },
      router: { rawBytes: 36546, gzipBytes: 13236 }
    },
    requiredRuntime: { rawBytes: 229187, gzipBytes: 73544 },
    eagerApplication: { rawBytes: 38956, gzipBytes: 11312 },
    lazyJavaScript: { rawBytes: 59936, gzipBytes: 0 },
    initial: { files: ["assets/entry.js", "assets/react-vendor-abc.js"], rawBytes: 269547, gzipBytes: 84854 },
    totalJavaScript: { files: ["assets/entry.js"], rawBytes: 329483 }
  };

  expect(evaluateBudgets({
    report,
    budgets: REVISED_BUDGETS,
    expectedRouteSources: EXPECTED_ROUTE_SOURCES,
    html: "<html></html>",
    reviewedIdentity: REVIEWED_IDENTITY,
    reviewedRuntimeComponents: REVIEWED_RUNTIME_COMPONENTS
  })).toEqual([]);
});

it("fails closed when revised attribution evidence is missing", () => {
  const report = {
    dynamicEntries: EXPECTED_ROUTE_SOURCES.map((source) => ({
      file: `assets/${source}.js`,
      source: `src/pages/${source}`
    })),
    identity: REVIEWED_IDENTITY,
    initial: { files: ["assets/entry.js", "assets/react-vendor-abc.js"], rawBytes: 269547, gzipBytes: 84854 },
    totalJavaScript: { files: ["assets/entry.js"], rawBytes: 329483 }
  };

  const violations = evaluateBudgets({
    report,
    budgets: REVISED_BUDGETS,
    expectedRouteSources: EXPECTED_ROUTE_SOURCES,
    html: "<html></html>",
    reviewedIdentity: REVIEWED_IDENTITY,
    reviewedRuntimeComponents: REVIEWED_RUNTIME_COMPONENTS
  });

  expect(violations).toContain("Required runtime attribution is missing.");
  expect(violations).toContain("Eager application attribution is missing.");
  expect(violations).toContain("Lazy-route attribution is missing.");
  expect(violations).toContain("Required runtime measurement is missing.");
});

it("rejects ambiguous lazy-route ownership", () => {
  const report = {
    dynamicEntries: EXPECTED_ROUTE_SOURCES.map((source, index) => ({
      file: index === 1 ? "assets/SignalListPage.tsx.js" : `assets/${source}.js`,
      source: `src/pages/${source}`
    })),
    identity: REVIEWED_IDENTITY,
    requiredRuntime: { rawBytes: 229187, gzipBytes: 73544 },
    eagerApplication: { rawBytes: 38956, gzipBytes: 11312 },
    lazyJavaScript: { rawBytes: 59936, gzipBytes: 0 },
    initial: { files: ["assets/entry.js", "assets/react-vendor-abc.js"], rawBytes: 269547, gzipBytes: 84854 },
    totalJavaScript: { files: ["assets/entry.js"], rawBytes: 329483 }
  };

  const violations = evaluateBudgets({
    report,
    budgets: REVISED_BUDGETS,
    expectedRouteSources: EXPECTED_ROUTE_SOURCES,
    html: "<html></html>",
    reviewedIdentity: REVIEWED_IDENTITY
  });

  expect(violations).toContain("Lazy route entries must map to distinct chunk files.");
});
