import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { Pagination } from "./Pagination";

it("states which rows are on screen when the total is known", () => {
  render(
    <Pagination
      itemCount={20}
      offset={20}
      onOffsetChange={() => undefined}
      pageSize={20}
      totalCount={137}
    />
  );

  expect(screen.getByRole("status")).toHaveTextContent("Showing 21–40 of 137.");
});

it("states the range without a total when the endpoint does not report one", () => {
  render(
    <Pagination itemCount={10} offset={0} onOffsetChange={() => undefined} pageSize={10} />
  );

  expect(screen.getByRole("status")).toHaveTextContent("Showing 1–10.");
});

it("says so when the offset has no rows", () => {
  render(
    <Pagination itemCount={0} offset={400} onOffsetChange={() => undefined} pageSize={20} />
  );

  expect(screen.getByRole("status")).toHaveTextContent("No rows at this offset.");
});

it("declares its button variant and is reachable as a labeled navigation region", () => {
  render(
    <Pagination itemCount={10} offset={0} onOffsetChange={() => undefined} pageSize={10} />
  );

  const region = screen.getByRole("navigation", { name: "Pagination" });
  expect(region).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Previous" })).toHaveClass("button-secondary");
  expect(screen.getByRole("button", { name: "Next" })).toHaveClass("button-secondary");
});

it("disables Previous on the first page and Next at the end of a known total", () => {
  const onOffsetChange = vi.fn();
  render(
    <Pagination
      itemCount={10}
      offset={0}
      onOffsetChange={onOffsetChange}
      pageSize={10}
      totalCount={10}
    />
  );

  expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();

  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  expect(onOffsetChange).not.toHaveBeenCalled();
});

it("steps by one page in each direction", () => {
  const onOffsetChange = vi.fn();
  render(
    <Pagination itemCount={10} offset={20} onOffsetChange={onOffsetChange} pageSize={10} />
  );

  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  expect(onOffsetChange).toHaveBeenLastCalledWith(30);

  fireEvent.click(screen.getByRole("button", { name: "Previous" }));
  expect(onOffsetChange).toHaveBeenLastCalledWith(10);
});
