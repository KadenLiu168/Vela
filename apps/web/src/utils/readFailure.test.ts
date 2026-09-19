import { describe, expect, it } from "vitest";
import { ApiClientError } from "../api/client";
import { describeReadFailure } from "./readFailure";

const NETWORK_MARKERS = /http|network/i;

describe("describeReadFailure", () => {
  it("names the unreachable API and the action that recovers it", () => {
    const message = describeReadFailure(new ApiClientError("offline", { kind: "network" }));

    expect(message).toContain("The local API could not be reached");
    expect(message).toContain("running");
    expect(message).toContain("retry");
  });

  it("reports the numeric status of an error response", () => {
    const message = describeReadFailure(
      new ApiClientError("boom", { kind: "http", status: 500, category: "unexpected" })
    );

    expect(message).toContain("API returned an error response");
    expect(message).toContain("500");
  });

  it("distinguishes distinct error statuses", () => {
    const serverError = describeReadFailure(
      new ApiClientError("boom", { kind: "http", status: 500, category: "unexpected" })
    );
    const validationError = describeReadFailure(
      new ApiClientError("bad", { kind: "http", status: 422, category: "validation" })
    );

    expect(serverError).not.toEqual(validationError);
    expect(validationError).toContain("422");
  });

  it("handles a non-ApiClientError failure without inventing a cause", () => {
    expect(describeReadFailure(new Error("kaboom"))).toBe(
      "The request failed for an unknown reason."
    );
    expect(describeReadFailure(undefined)).toBe("The request failed for an unknown reason.");
  });

  it("never exposes the internal failure category", () => {
    const failures = [
      new ApiClientError("offline", { kind: "network" }),
      new ApiClientError("boom", { kind: "http", status: 500, category: "unexpected" }),
      new ApiClientError("bad", { kind: "http", status: 422, category: "validation" }),
      new ApiClientError("gone", { kind: "http", status: 404, category: "not_found" }),
      new Error("kaboom"),
      "not an error"
    ];

    for (const failure of failures) {
      expect(describeReadFailure(failure)).not.toMatch(NETWORK_MARKERS);
    }
  });
});
