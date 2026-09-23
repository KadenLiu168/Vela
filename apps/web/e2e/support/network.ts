/*
 * Network isolation for the acceptance workflow.
 *
 * Every browser request is intercepted at the context level:
 *   - the static server origin (runner) serves pages/assets itself;
 *   - `/api` requests on that origin MUST match an explicit fixture
 *     (method + path template + exact query map) and are fulfilled in memory;
 *   - everything else (unmatched `/api`, any other origin — including other
 *     local ports) is recorded and aborted, failing the run afterwards.
 * Service workers are blocked twice: via the context `serviceWorkers: "block"`
 * option and via an init script that removes `navigator.serviceWorker`, so a
 * worker can never bypass interception.
 */
import type { BrowserContext, Route } from "@playwright/test";

export type ApiFixtureSpec = {
  method: "GET" | "POST";
  /** Path template with `{param}` segments, always starting with `/api/`. */
  path: string;
  /** Exact query map. Requests must carry exactly these params. */
  query?: Record<string, string>;
  status?: number;
  /** JSON body, or a function of the parsed URL. */
  body: unknown | ((url: URL) => unknown);
  /** Optional artificial latency for loading-state fixtures. */
  delayMs?: number;
};

type RecordedRequest = {
  method: string;
  url: string;
  pathname: string;
};

export class ApiRegistry {
  readonly fixtures: ApiFixtureSpec[];
  /** `/api` requests with no matching fixture (aborted). */
  readonly unmatched: RecordedRequest[] = [];
  /** Requests to other origins, blocked before leaving the browser. */
  readonly blocked: RecordedRequest[] = [];
  private declaredUnmatched = new Set<string>();
  private declaredBlocked = new Set<string>();

  constructor(fixtures: ApiFixtureSpec[] = []) {
    this.fixtures = fixtures;
  }

  /** Declare an expected-unmatched `/api` probe (isolation verification). */
  declareUnmatched(method: string, pathname: string): void {
    this.declaredUnmatched.add(`${method} ${pathname}`);
  }

  /** Declare an expected cross-origin block (isolation verification). */
  declareBlocked(method: string, url: string): void {
    this.declaredBlocked.add(`${method} ${url}`);
  }

  match(method: string, url: URL): ApiFixtureSpec | null {
    const pathSegments = url.pathname.split("/").filter(Boolean);

    for (const fixture of this.fixtures) {
      if (fixture.method !== method) {
        continue;
      }

      const templateSegments = fixture.path.split("/").filter(Boolean);
      if (templateSegments.length !== pathSegments.length) {
        continue;
      }

      let matches = true;
      for (let index = 0; index < templateSegments.length; index += 1) {
        const template = templateSegments[index];
        const actual = pathSegments[index];
        if (template.startsWith("{") && template.endsWith("}")) {
          continue;
        }
        if (template !== actual) {
          matches = false;
          break;
        }
      }
      if (!matches) {
        continue;
      }

      // Query must match exactly: every declared param present with the same
      // value, and no extra params.
      const declared = fixture.query ?? {};
      const incoming = Object.fromEntries(url.searchParams.entries());
      const declaredKeys = Object.keys(declared);
      const incomingKeys = Object.keys(incoming);
      if (declaredKeys.length !== incomingKeys.length) {
        continue;
      }
      if (declaredKeys.every((key) => key in incoming && incoming[key] === declared[key])) {
        return fixture;
      }
    }

    return null;
  }

  /** Throws when an undeclared unmatched or blocked request was recorded. */
  assertNoUnexpected(): void {
    const problems: string[] = [];

    for (const request of this.unmatched) {
      const key = `${request.method} ${request.pathname}`;
      if (!this.declaredUnmatched.has(key)) {
        problems.push(`unmatched API request: ${request.method} ${request.url}`);
      }
    }
    for (const request of this.blocked) {
      const key = `${request.method} ${request.url}`;
      if (!this.declaredBlocked.has(key)) {
        problems.push(`blocked request to non-allowed origin: ${request.method} ${request.url}`);
      }
    }

    if (problems.length > 0) {
      throw new Error(
        `fail-closed network guard tripped:\n${problems.join("\n")}`
      );
    }
  }

  reset(): void {
    this.unmatched.length = 0;
    this.blocked.length = 0;
    this.declaredUnmatched.clear();
    this.declaredBlocked.clear();
  }
}

/** Parses a request URL; returns null when the input is not a valid URL. */
function parseUrl(raw: string): URL | null {
  try {
    return new URL(raw);
  } catch {
    return null;
  }
}

export async function installNetworkIsolation(
  context: BrowserContext,
  registry: ApiRegistry,
  allowedOrigin: string
): Promise<void> {
  await context.route("**/*", (route: Route) => {
    const request = route.request();
    const url = parseUrl(request.url());
    if (url === null) {
      // Fail closed: an unparseable URL cannot match any fixture.
      registry.blocked.push({ method: request.method(), url: request.url(), pathname: "<unparseable>" });
      void route.abort("failed");
      return;
    }

    if (url.origin !== allowedOrigin) {
      registry.blocked.push({
        method: request.method(),
        url: request.url(),
        pathname: url.pathname
      });
      void route.abort("failed");
      return;
    }

    if (url.pathname === "/api" || url.pathname.startsWith("/api/")) {
      const fixture = registry.match(request.method(), url);
      if (fixture === null) {
        registry.unmatched.push({
          method: request.method(),
          url: request.url(),
          pathname: url.pathname
        });
        void route.abort("failed");
        return;
      }

      const body =
        typeof fixture.body === "function"
          ? (fixture.body as (url: URL) => unknown)(url)
          : fixture.body;

      const fulfill = () => {
        void route.fulfill({
          status: fixture.status ?? 200,
          contentType: "application/json",
          body: JSON.stringify(body)
        });
      };

      if (fixture.delayMs === undefined) {
        fulfill();
      } else {
        setTimeout(fulfill, fixture.delayMs);
      }
      return;
    }

    // Same-origin page asset: continue through the static server.
    void route.fallback();
  });

  // Service-worker isolation: a worker could otherwise issue requests that
  // bypass per-page interception.
  await context.addInitScript(() => {
    Object.defineProperty(navigator, "serviceWorker", {
      get: () => undefined,
      configurable: true
    });
  });
}
