import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { Pagination } from "./Pagination";

it("keeps the existing inferred next-page behavior when totalCount is omitted", () => {
  render(<Pagination itemCount={20} offset={0} onOffsetChange={vi.fn()} pageSize={20} />);

  expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Next" })).toBeEnabled();
});

it("uses totalCount to disable Next on a partial final page", () => {
  render(<Pagination itemCount={3} offset={20} onOffsetChange={vi.fn()} pageSize={20} totalCount={23} />);

  expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
});

it("uses totalCount to disable Next when total is an exact page multiple", () => {
  const onOffsetChange = vi.fn();
  render(<Pagination itemCount={20} offset={20} onOffsetChange={onOffsetChange} pageSize={20} totalCount={40} />);

  expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Previous" }));
  expect(onOffsetChange).toHaveBeenCalledWith(0);
});
