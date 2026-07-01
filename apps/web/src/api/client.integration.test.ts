import { expect, it } from "vitest";
import {
  fetchFullMarketData,
  fetchIncrementalMarketData,
  generateStrategySignal,
  getDashboard,
  getHealth,
  getLatestStrategySignal
} from "./client";

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

it.runIf(import.meta.env.VITE_API_BASE_URL)(
  "calls local API full market data fetch through the shared client",
  async () => {
    const result = await fetchFullMarketData();

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

it.runIf(import.meta.env.VITE_API_BASE_URL)(
  "calls local API strategy signal generation through the shared client",
  async () => {
    const result = await generateStrategySignal();
    const dashboard = await getDashboard();
    const latestSignal = await getLatestStrategySignal();

    expect(result).toMatchObject({
      signal_id: expect.any(Number),
      signal_date: expect.any(String),
      config_version: expect.any(String),
      status: expect.any(String),
      positions: expect.any(Array)
    });
    expect(Object.prototype.hasOwnProperty.call(result, "error_message")).toBe(true);
    expect(result.error_message === null || typeof result.error_message === "string").toBe(true);
    expect(dashboard.latest_signal).toMatchObject({
      signal_id: result.signal_id,
      signal_date: result.signal_date,
      status: result.status
    });
    expect(latestSignal.signal).toMatchObject({
      signal_id: result.signal_id,
      signal_date: result.signal_date
    });
    expect(latestSignal.positions).toHaveLength(result.positions.length);
  }
);

it.runIf(import.meta.env.VITE_API_BASE_URL)(
  "calls local API latest strategy signal through the shared client",
  async () => {
    const result = await getLatestStrategySignal();

    expect(result).toMatchObject({
      has_signal: expect.any(Boolean),
      positions: expect.any(Array)
    });

    if (result.has_signal) {
      expect(result.signal).toMatchObject({
        signal_id: expect.any(Number),
        signal_date: expect.any(String),
        config_version: expect.any(String),
        generated_at: expect.any(String),
        is_fallback: expect.any(Boolean)
      });
    } else {
      expect(result.signal).toBeNull();
      expect(result.positions).toEqual([]);
    }
  }
);
