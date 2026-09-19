import { renderHook } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { formatDocumentTitle, useDocumentTitle } from "./documentTitle";

afterEach(() => {
  document.title = "";
});

it("appends the brand to the page identity", () => {
  expect(formatDocumentTitle("Signals")).toBe("Signals · Vela Research");
});

it("sets the document title from the hook", () => {
  renderHook(() => useDocumentTitle("Backtests"));

  expect(document.title).toBe("Backtests · Vela Research");
});

it("updates the title when the page identity changes", () => {
  const { rerender } = renderHook(({ identity }) => useDocumentTitle(identity), {
    initialProps: { identity: "Signals" }
  });

  expect(document.title).toBe("Signals · Vela Research");

  rerender({ identity: "Signal Detail #307" });

  expect(document.title).toBe("Signal Detail #307 · Vela Research");
});
