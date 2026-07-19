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
