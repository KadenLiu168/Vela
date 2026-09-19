/**
 * A history-list row records where it was clicked from, so the detail page's
 * own back link can return to the same page and filter instead of sending the
 * user to the unfiltered first page — the browser's Back control already keeps
 * that context, and the link the app itself offers should not be worse.
 *
 * The value comes from Router location state, so a direct visit, a bookmark, or
 * a reload without state falls back to the list's own path.
 */
export function listReturnHref(state: unknown, fallback: string): string {
  if (typeof state === "object" && state !== null) {
    const href = (state as { listHref?: unknown }).listHref;
    // A single leading slash keeps this an in-application path; `//host` would
    // be a protocol-relative URL that leaves the application.
    if (typeof href === "string" && href.startsWith("/") && !href.startsWith("//")) {
      return href;
    }
  }

  return fallback;
}
