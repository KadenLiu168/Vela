import { gzipSync } from "node:zlib";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, expect, it } from "vitest";
import { analyzeManifest } from "./bundle-manifest.mjs";

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
