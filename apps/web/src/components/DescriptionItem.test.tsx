import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { DescriptionItem } from "./DescriptionItem";

it("renders sibling description terms and values without a layout wrapper", () => {
  const { container } = render(
    <dl>
      <DescriptionItem
        label="Backtest"
        value={<a href="/backtests/8">Backtest #8</a>}
      />
    </dl>
  );

  const list = container.querySelector("dl");
  expect(list?.children).toHaveLength(2);
  expect(list?.firstElementChild?.tagName).toBe("DT");
  expect(list?.lastElementChild?.tagName).toBe("DD");
  expect(screen.getByRole("link", { name: "Backtest #8" })).toHaveAttribute("href", "/backtests/8");
});

it("marks quantitative values with the mono data class and leaves language values Sans", () => {
  const { container } = render(
    <dl>
      <DescriptionItem label="Signal date" value="2026-08-12" mono />
      <DescriptionItem label="Status" value="completed" />
    </dl>
  );

  const values = container.querySelectorAll("dd");
  expect(values[0]).toHaveClass("mono-compact");
  expect(values[1]).not.toHaveClass("mono-compact");
});
