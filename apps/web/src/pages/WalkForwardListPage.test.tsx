import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ApiClientError, listWalkForwards } from "../api/client";
import { WalkForwardListPage } from "./WalkForwardListPage";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, listWalkForwards: vi.fn() };
});

const listMock = vi.mocked(listWalkForwards);

afterEach(() => vi.clearAllMocks());

const summary = (runId: number) => ({
  run_id: runId,
  strategy_id: "dual_momentum",
  start_date: "2026-01-01",
  end_date: "2026-12-31",
  window_count: 3,
  provenance_version: "wf_provenance_v1",
  evidence_version: "wf_evidence_v1",
  config_checksum: "a".repeat(64),
  input_data_checksum: "b".repeat(64),
  started_at: "2026-12-01T00:00:00",
  finished_at: "2026-12-02T00:00:00"
});

it("renders history metadata and links rows to detail", async () => {
  listMock.mockResolvedValue({ runs: [summary(8)], total: 1, limit: 10, offset: 0 });

  render(<WalkForwardListPage />);

  expect(await screen.findByText("Walk-forward History")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "#8" })).toHaveAttribute("href", "/walk-forwards/8");
  expect(screen.getByText(/wf_provenance_v1 \/ wf_evidence_v1/)).toBeInTheDocument();
  expect(listMock).toHaveBeenCalledWith(10, 0);
});

it("uses the exact total at the final page boundary", async () => {
  listMock.mockImplementation(async (_limit, offset = 0) => ({
    runs: [summary(offset === 10 ? 18 : 8)],
    total: 11,
    limit: 10,
    offset
  }));
  render(<WalkForwardListPage />);

  await screen.findByText("#8");
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  await screen.findByText("#18");
  expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "Previous" })).not.toBeDisabled();
});

it("shows an explicit error and suppresses stale results after a failed request", async () => {
  listMock.mockResolvedValueOnce({ runs: [summary(8)], total: 11, limit: 10, offset: 0 });
  listMock.mockRejectedValueOnce(new ApiClientError("unavailable", { kind: "network" }));
  render(<WalkForwardListPage />);
  await screen.findByText("#8");
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("unavailable"));
  expect(screen.queryByText("#8")).not.toBeInTheDocument();
});
