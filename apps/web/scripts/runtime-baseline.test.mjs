// @vitest-environment node
import { expect, it } from "vitest";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { TextDecoder, TextEncoder } from "node:util";

process.env.NODE_ENV = "production";
globalThis.TextEncoder = TextEncoder;
globalThis.TextDecoder = TextDecoder;
const { measureIsolatedRuntime } = await import("./runtime-baseline.mjs");

it("measures React and Router runtime chunks from an isolated build", async () => {
  const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  const measurement = await measureIsolatedRuntime(webRoot);

  expect(measurement.reactVendor.rawBytes).toBeGreaterThan(0);
  expect(measurement.reactVendor.gzipBytes).toBeGreaterThan(0);
  expect(measurement.reactVendor.rawBytes).toBe(192347);
  // gzip output depends on the runtime zlib version: identical chunk content
  // measures 60212 bytes under zlib 1.2.x (node 25) and 60287 under zlib
  // 1.3.x (node 22). Keep an environment-agnostic ceiling so the check guards
  // against runtime bloat instead of false-failing on zlib differences; the
  // exact rawBytes assertion above remains the content guard.
  expect(measurement.reactVendor.gzipBytes).toBeGreaterThanOrEqual(59000);
  expect(measurement.reactVendor.gzipBytes).toBeLessThanOrEqual(62000);
  expect(measurement.router.rawBytes).toBeLessThanOrEqual(36840);
  expect(measurement.router.gzipBytes).toBeLessThanOrEqual(13332);
});
