import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import App from "./App";

it("renders the web app skeleton", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: "Vela Web" })).toBeInTheDocument();
  expect(screen.getByText("Frontend skeleton ready")).toBeInTheDocument();
});
