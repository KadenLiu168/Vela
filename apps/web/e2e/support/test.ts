/*
 * Shared Playwright test extension.
 *
 * Every test gets a per-test API registry with the network-isolation route
 * handler installed. After each test the registry asserts that no undeclared
 * unmatched `/api` request or cross-origin request occurred, so a stray
 * request fails the test instead of reaching a real service.
 *
 * Tests that need state variants override specific fixtures via the
 * `fixtures` option; overridden fixtures are matched first.
 */
import { test as base, expect } from "@playwright/test";
import { ApiRegistry, installNetworkIsolation, type ApiFixtureSpec } from "./network.ts";
import { populatedFixtures, operationFixtures } from "../fixtures/apiFixtures.ts";

export type TestFixtures = {
  /** Per-test API fixture registry; populated by default. */
  api: ApiRegistry;
  /** Fixture overrides; matching happens before the default populated set. */
  fixtures?: ApiFixtureSpec[];
};

export const test = base.extend<TestFixtures, object>({
  fixtures: [undefined, { option: true }],

  api: [
    async ({ context, baseURL, fixtures }, provide) => {
      const registry = new ApiRegistry([
        ...(fixtures ?? []),
        ...populatedFixtures(),
        ...operationFixtures()
      ]);
      await installNetworkIsolation(context, registry, baseURL ?? "");
      await provide(registry);
      registry.assertNoUnexpected();
      registry.reset();
    },
    // auto: network isolation applies to every test, even those that never
    // touch `api` directly.
    { auto: true }
  ]
});

export { expect };
