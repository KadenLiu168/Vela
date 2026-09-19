import { expect, it } from "vitest";
import { isValidListOffset, listHrefWith, listOffsetFrom } from "./listQuery";

it("accepts non-negative decimal offsets", () => {
  expect(isValidListOffset("0")).toBe(true);
  expect(isValidListOffset("40")).toBe(true);
  expect(listOffsetFrom("40")).toBe(40);
  expect(listOffsetFrom("0")).toBe(0);
});

it("rejects absent, negative, fractional, and non-numeric offsets", () => {
  for (const value of [null, "", "-1", "1.5", "abc", "20px", " "]) {
    expect(isValidListOffset(value)).toBe(false);
    expect(listOffsetFrom(value)).toBe(0);
  }
});

it("writes, replaces, and drops parameters while keeping the hash", () => {
  const location = { pathname: "/signals", search: "?source=manual&keep=yes", hash: "#rows" };

  expect(listHrefWith(location, { offset: "20" })).toBe("/signals?source=manual&keep=yes&offset=20#rows");
  expect(listHrefWith(location, { offset: null })).toBe("/signals?source=manual&keep=yes#rows");
  // Replacing an existing parameter keeps its position in the query.
  expect(listHrefWith(location, { source: "backtest", offset: null })).toBe(
    "/signals?source=backtest&keep=yes#rows"
  );
});

it("omits the query entirely when nothing is left", () => {
  expect(listHrefWith({ pathname: "/backtests", search: "?offset=20", hash: "" }, { offset: null })).toBe(
    "/backtests"
  );
});
