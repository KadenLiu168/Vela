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
  expect(measurement.reactVendor.gzipBytes).toBe(60212);
  expect(measurement.router.rawBytes).toBeLessThanOrEqual(36840);
  expect(measurement.router.gzipBytes).toBeLessThanOrEqual(13332);
});
