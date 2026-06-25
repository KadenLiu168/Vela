import { expect, it } from "vitest";
import { getHealth } from "./client";

it.runIf(import.meta.env.VITE_API_BASE_URL)(
  "calls local API health through the shared client",
  async () => {
    await expect(getHealth()).resolves.toEqual({ status: "healthy" });
  }
);
