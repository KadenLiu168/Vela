import { ApiClientError } from "../api/client";

/**
 * Turns a failed read into a sentence the user can act on. The two failure
 * modes that actually occur locally are kept distinct on purpose: an API
 * process that is not running is the common case and has a concrete next
 * step, while an error response has a status the user needs to see.
 *
 * The internal `ApiClientError.kind` values (`http` / `network`) are never
 * rendered; they identify the failure to the caller, not to the user.
 */
export function describeReadFailure(error: unknown): string {
  if (error instanceof ApiClientError && error.kind === "network") {
    return "The local API could not be reached. Check that the API service is running, then retry.";
  }

  if (error instanceof ApiClientError && error.status !== undefined) {
    return `The API returned an error response (${error.status}).`;
  }

  return "The request failed for an unknown reason.";
}
