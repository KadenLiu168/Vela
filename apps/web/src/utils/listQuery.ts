const OFFSET_PATTERN = /^\d+$/;

type ListLocation = {
  pathname: string;
  search: string;
  hash: string;
};

/** A list offset is addressable through the URL only as a non-negative
 *  decimal integer; anything else is normalized away by the page. */
export function isValidListOffset(value: string | null): value is string {
  return value !== null && OFFSET_PATTERN.test(value);
}

export function listOffsetFrom(value: string | null): number {
  return isValidListOffset(value) ? Number(value) : 0;
}

/**
 * Rewrites this list's query string, preserving unrelated parameters and the
 * hash. A `null` value removes that parameter, which is how a list says "back
 * to the default" — the first page and the All filter are both the absence of
 * their parameter rather than an explicit default value.
 *
 * All three history lists own their query state this way, so the rule for
 * whether a value is written, replaced, or dropped lives in one place instead
 * of once per page.
 */
export function listHrefWith(
  location: ListLocation,
  changes: Record<string, string | null>
): string {
  const params = new URLSearchParams(location.search);
  for (const [name, value] of Object.entries(changes)) {
    if (value === null) {
      params.delete(name);
    } else {
      params.set(name, value);
    }
  }

  const search = params.toString();
  return `${location.pathname}${search ? `?${search}` : ""}${location.hash}`;
}
