import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClientError, apiRequest, getHealth } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("returns parsed JSON for successful responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "healthy" }), {
          headers: { "Content-Type": "application/json" },
          status: 200
        })
      )
    );

    await expect(apiRequest<{ status: string }>("/health")).resolves.toEqual({
      status: "healthy"
    });
  });

  it("normalizes HTTP errors with status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "not found" }), {
          headers: { "Content-Type": "application/json" },
          status: 404
        })
      )
    );

    await expect(apiRequest("/missing")).rejects.toMatchObject({
      kind: "http",
      status: 404,
      message: "not found"
    });
  });

  it("normalizes network errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("failed")));

    await expect(apiRequest("/health")).rejects.toMatchObject({
      kind: "network",
      message: "Network request failed"
    });
  });
});

it("calls health through the shared client", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ status: "healthy" }), {
      headers: { "Content-Type": "application/json" },
      status: 200
    })
  );
  vi.stubGlobal("fetch", fetchMock);

  await expect(getHealth()).resolves.toEqual({ status: "healthy" });
  expect(fetchMock).toHaveBeenCalledWith("/api/health", undefined);
});

it("exposes a typed API client error", () => {
  const error = new ApiClientError("HTTP request failed", { kind: "http", status: 500 });

  expect(error).toMatchObject({
    kind: "http",
    status: 500,
    message: "HTTP request failed"
  });
});
