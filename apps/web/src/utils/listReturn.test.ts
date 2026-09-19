import { expect, it } from "vitest";
import { listReturnHref } from "./listReturn";

it("returns the originating list location when the row recorded one", () => {
  expect(listReturnHref({ listHref: "/signals?source=manual&offset=40" }, "/signals")).toBe(
    "/signals?source=manual&offset=40"
  );
});

it("falls back when there is no recorded location", () => {
  expect(listReturnHref(null, "/signals")).toBe("/signals");
  expect(listReturnHref(undefined, "/signals")).toBe("/signals");
  expect(listReturnHref({}, "/signals")).toBe("/signals");
  expect(listReturnHref({ listHref: 42 }, "/signals")).toBe("/signals");
});

it("refuses a non-application destination", () => {
  expect(listReturnHref({ listHref: "https://example.com/x" }, "/signals")).toBe("/signals");
  expect(listReturnHref({ listHref: "//evil.example" }, "/signals")).toBe("/signals");
});
