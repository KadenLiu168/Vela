const DEFAULT_API_BASE_URL = "/api";

type ApiClientErrorOptions =
  | {
      kind: "http";
      status: number;
    }
  | {
      kind: "network";
      status?: never;
    };

export class ApiClientError extends Error {
  kind: ApiClientErrorOptions["kind"];
  status?: number;

  constructor(message: string, options: ApiClientErrorOptions) {
    super(message);
    this.name = "ApiClientError";
    this.kind = options.kind;
    this.status = options.kind === "http" ? options.status : undefined;
  }
}

export type HealthResponse = {
  status: string;
};

export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
  baseUrl = getApiBaseUrl()
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${baseUrl}${path}`, init);
  } catch {
    throw new ApiClientError("Network request failed", { kind: "network" });
  }

  if (!response.ok) {
    throw new ApiClientError(await getErrorMessage(response), {
      kind: "http",
      status: response.status
    });
  }

  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();

    if (isObjectWithStringDetail(body)) {
      return body.detail;
    }
  } catch {
    return response.statusText || "HTTP request failed";
  }

  return response.statusText || "HTTP request failed";
}

function isObjectWithStringDetail(value: unknown): value is { detail: string } {
  return (
    typeof value === "object" &&
    value !== null &&
    "detail" in value &&
    typeof value.detail === "string"
  );
}
