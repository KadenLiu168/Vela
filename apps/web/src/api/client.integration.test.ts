import { expect, it } from "vitest";
import { fetchIncrementalMarketData, getHealth } from "./client";

it.runIf(import.meta.env.VITE_API_BASE_URL)(
  "calls local API health through the shared client",
  async () => {
    await expect(getHealth()).resolves.toEqual({ status: "healthy" });
  }
);

it.runIf(import.meta.env.VITE_API_BASE_URL)(
  "calls local API incremental market data fetch through the shared client",
  async () => {
    const result = await fetchIncrementalMarketData();

    expect(result).toMatchObject({
      status: expect.any(String),
      requested_etf_count: expect.any(Number),
      rows_fetched: expect.any(Number),
      rows_inserted: expect.any(Number),
      rows_updated: expect.any(Number),
      failed_symbols: expect.any(Array)
    });
    expect(Object.prototype.hasOwnProperty.call(result, "error_message")).toBe(true);
    expect(result.error_message === null || typeof result.error_message === "string").toBe(true);
  }
);
