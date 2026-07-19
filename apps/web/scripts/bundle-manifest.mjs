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

export async function analyzeManifest({ manifest, outputDirectory }) {
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
  const dynamicEntries = entries
    .filter(([, entry]) => entry.isDynamicEntry)
    .map(([key, entry]) => ({ file: entry.file, source: entry.src ?? key }));

  return {
    dynamicEntries,
    initial: await measureFiles(outputDirectory, initialFiles),
    initialKeys: [...initialKeys],
    totalJavaScript: await measureFiles(outputDirectory, allJavaScriptFiles)
  };
}
