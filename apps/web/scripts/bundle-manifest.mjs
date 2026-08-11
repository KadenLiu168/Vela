import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

function isJavaScript(file) {
  return file.endsWith(".js");
}

async function measureFiles(outputDirectory, files) {
  const measurements = await Promise.all(
    files.map(async (file) => {
      const contents = await readFile(join(outputDirectory, file));
      return { file, gzipBytes: gzipSync(contents).length, rawBytes: contents.length };
    })
  );

  return {
    files,
    gzipBytes: measurements.reduce((total, measurement) => total + measurement.gzipBytes, 0),
    rawBytes: measurements.reduce((total, measurement) => total + measurement.rawBytes, 0)
  };
}

export async function analyzeManifest({
  manifest,
  outputDirectory,
  identity,
  requiredRuntime = { rawBytes: 0, gzipBytes: 0 },
  runtimeMeasurement
}) {
  const entries = Object.entries(manifest);
  const entryKey = entries.find(([, entry]) => entry.isEntry)?.[0];

  if (!entryKey) {
    throw new Error("Vite manifest does not contain a client entry.");
  }

  const initialKeys = new Set();
  const visitStaticImports = (key) => {
    if (initialKeys.has(key)) return;
    initialKeys.add(key);
    for (const importKey of manifest[key]?.imports ?? []) {
      visitStaticImports(importKey);
    }
  };
  visitStaticImports(entryKey);

  const initialFiles = [...initialKeys]
    .map((key) => manifest[key]?.file)
    .filter(isJavaScript);
  const allJavaScriptFiles = [...new Set(entries.map(([, entry]) => entry.file).filter(isJavaScript))];
  const initial = await measureFiles(outputDirectory, initialFiles);
  const lazyJavaScript = await measureFiles(
    outputDirectory,
    allJavaScriptFiles.filter((file) => !initial.files.includes(file))
  );
  const dynamicEntries = entries
    .filter(([, entry]) => entry.isDynamicEntry)
    .map(([key, entry]) => ({ file: entry.file, source: entry.src ?? key }));

  return {
    dynamicEntries,
    identity,
    requiredRuntime,
    runtimeMeasurement,
    eagerApplication: {
      rawBytes: initial.rawBytes - requiredRuntime.rawBytes,
      gzipBytes: initial.gzipBytes - requiredRuntime.gzipBytes
    },
    initial,
    initialKeys: [...initialKeys],
    lazyJavaScript,
    totalJavaScript: await measureFiles(outputDirectory, allJavaScriptFiles)
  };
}

function identityMatches(actual, expected) {
  return ["node", "npm", "vite", "lockfile"].every((field) => actual?.[field] === expected?.[field]);
}

export function evaluateBudgets({ report, budgets, expectedRouteSources, html, reviewedIdentity, reviewedRuntimeComponents }) {
  const violations = [];

  if (reviewedIdentity && !identityMatches(report.identity, reviewedIdentity)) {
    violations.push("Build identity does not match the reviewed identity.");
  }

  if (reviewedRuntimeComponents) {
    const measurement = report.runtimeMeasurement;
    if (!measurement) {
      violations.push("Required runtime measurement is missing.");
    } else {
      for (const component of ["reactVendor", "router"]) {
        for (const metric of ["rawBytes", "gzipBytes"]) {
          const actual = measurement[component]?.[metric];
          const reviewed = reviewedRuntimeComponents[component]?.[metric];
          if (!Number.isFinite(actual)) {
            violations.push(`Measured ${component} ${metric} is missing.`);
          } else if (Number.isFinite(reviewed) && actual > reviewed) {
            violations.push(`Measured ${component} ${metric} is ${actual} bytes, above the reviewed ${reviewed}-byte component baseline.`);
          }
        }
      }
    }
  }

  if (budgets.requiredRuntimeRaw !== undefined) {
    const actual = report.requiredRuntime?.rawBytes;
    if (!Number.isFinite(actual)) {
      violations.push("Required runtime attribution is missing.");
    } else if (actual > budgets.requiredRuntimeRaw) {
      violations.push(`Required runtime raw JavaScript is ${actual} bytes, above the ${budgets.requiredRuntimeRaw}-byte baseline.`);
    } else if (actual < budgets.requiredRuntimeRaw) {
      violations.push(`Required runtime raw JavaScript is ${actual} bytes, below the ${budgets.requiredRuntimeRaw}-byte baseline.`);
    }
  }
  if (budgets.requiredRuntimeGzip !== undefined) {
    const actual = report.requiredRuntime?.gzipBytes;
    if (!Number.isFinite(actual)) {
      if (!violations.includes("Required runtime attribution is missing.")) {
        violations.push("Required runtime attribution is missing.");
      }
    } else if (actual > budgets.requiredRuntimeGzip) {
      violations.push(`Required runtime gzip JavaScript is ${actual} bytes, above the ${budgets.requiredRuntimeGzip}-byte baseline.`);
    } else if (actual < budgets.requiredRuntimeGzip) {
      violations.push(`Required runtime gzip JavaScript is ${actual} bytes, below the ${budgets.requiredRuntimeGzip}-byte baseline.`);
    }
  }
  if (budgets.eagerApplicationRaw !== undefined) {
    const actual = report.eagerApplication?.rawBytes;
    if (!Number.isFinite(actual)) {
      violations.push("Eager application attribution is missing.");
    } else if (actual > budgets.eagerApplicationRaw) {
      violations.push(`Eager application raw JavaScript is ${actual} bytes, above the ${budgets.eagerApplicationRaw}-byte allocation.`);
    }
  }
  if (budgets.eagerApplicationGzip !== undefined) {
    const actual = report.eagerApplication?.gzipBytes;
    if (!Number.isFinite(actual)) {
      if (!violations.includes("Eager application attribution is missing.")) {
        violations.push("Eager application attribution is missing.");
      }
    } else if (actual > budgets.eagerApplicationGzip) {
      violations.push(`Eager application gzip JavaScript is ${actual} bytes, above the ${budgets.eagerApplicationGzip}-byte allocation.`);
    }
  }
  if (budgets.lazyRouteRaw !== undefined) {
    const actual = report.lazyJavaScript?.rawBytes;
    if (!Number.isFinite(actual)) {
      violations.push("Lazy-route attribution is missing.");
    } else if (actual > budgets.lazyRouteRaw) {
      violations.push(`Lazy-route JavaScript is ${actual} bytes, above the ${budgets.lazyRouteRaw}-byte allocation.`);
    }
  }

  if (report.initial.rawBytes > budgets.initialRaw) {
    violations.push(`Dashboard initial JavaScript is ${report.initial.rawBytes} bytes, above the ${budgets.initialRaw}-byte budget.`);
  }
  if (report.initial.gzipBytes > budgets.initialGzip) {
    violations.push(`Dashboard initial gzip JavaScript is ${report.initial.gzipBytes} bytes, above the ${budgets.initialGzip}-byte budget.`);
  }
  if (report.totalJavaScript.rawBytes > budgets.totalRaw) {
    violations.push(`Total JavaScript is ${report.totalJavaScript.rawBytes} bytes, above the ${budgets.totalRaw}-byte budget.`);
  }

  const initialFileSet = new Set(report.initial.files);
  const matchedRouteEntries = [];
  for (const source of expectedRouteSources) {
    const expectedSource = source.startsWith("src/") ? source : `src/pages/${source}`;
    const entry = report.dynamicEntries.find((candidate) => candidate.source === expectedSource);
    if (!entry) {
      violations.push(`Missing dynamic route entry for ${source}.`);
      continue;
    }
    matchedRouteEntries.push(entry);
    if (initialFileSet.has(entry.file)) {
      violations.push(`${source} is incorrectly included in the Dashboard static graph.`);
    }
    if (html.includes(entry.file)) {
      violations.push(`${source} is incorrectly module-preloaded by the Dashboard HTML.`);
    }
  }

  if (new Set(matchedRouteEntries.map((entry) => entry.file)).size !== matchedRouteEntries.length) {
    violations.push("Lazy route entries must map to distinct chunk files.");
  }

  if (!report.initial.files.some((file) => /(^|\/)react-vendor-[^/]+\.js$/.test(file))) {
    violations.push("Dashboard static graph does not include the react-vendor chunk.");
  }

  return violations;
}
