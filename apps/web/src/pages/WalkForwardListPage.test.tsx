import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  ApiClientError,
  getWalkForwardDetail,
  listWalkForwards,
  runWalkForward,
  type WalkForwardDetailResponse
} from "../api/client";
import { WalkForwardListPage } from "./WalkForwardListPage";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, listWalkForwards: vi.fn(), runWalkForward: vi.fn(), getWalkForwardDetail: vi.fn() };
});

const listMock = vi.mocked(listWalkForwards);
const runMock = vi.mocked(runWalkForward);
const detailMock = vi.mocked(getWalkForwardDetail);

afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
});

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
  status: "success" as const,
  error_message: null,
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

const runningDetail = (runId: number) => ({
  run: { ...summary(runId), status: "running" as const, finished_at: null, created_at: "2026-12-01T00:00:00" },
  configuration: {
    walk_forward: {},
    base_strategy: {},
    config_checksum: "a".repeat(64)
  },
  input_provenance: {
    manifest: {
      version: "wf_provenance_v1" as const,
      earliest_required_session: "2026-01-01",
      configured_end_date: "2026-12-31",
      following_session: null,
      official_sessions: ["2026-01-01", "2026-12-31"],
      active_etfs: [],
      loaded_price_row_count: 0,
      first_loaded_price_date: null,
      last_loaded_price_date: null
    },
    input_data_checksum: "b".repeat(64)
  },
  evidence_version: "wf_evidence_v1",
  evidence: null as unknown as WalkForwardDetailResponse["evidence"],
  windows: [],
  stitched_oos: {
    status: "unavailable_non_contiguous_windows" as const,
    initial_net_value: null,
    ending_net_value: null,
    total_return: null,
    points: []
  }
});

it("clicking Run calls runWalkForward and disables the button while pending", async () => {
  listMock.mockResolvedValue({ runs: [], total: 0, limit: 10, offset: 0 });
  runMock.mockResolvedValue({ walk_forward_run_id: 9 });
  render(<WalkForwardListPage />);
  await screen.findByText("Walk-forward History");

  const button = screen.getByRole("button", { name: "Run walk-forward" });
  fireEvent.click(button);

  expect(button).toBeDisabled();
  expect(runMock).toHaveBeenCalledTimes(1);
});

it("navigates to the detail page after polling reports success", async () => {
  listMock.mockResolvedValue({ runs: [], total: 0, limit: 10, offset: 0 });
  runMock.mockResolvedValue({ walk_forward_run_id: 9 });
  detailMock.mockResolvedValue({
    ...runningDetail(9),
    run: { ...summary(9), status: "success" as const, created_at: "2026-12-01T00:00:00" }
  });
  const pushSpy = vi.spyOn(window.history, "pushState");
  const popSpy = vi.spyOn(window, "dispatchEvent");

  render(<WalkForwardListPage />);
  await screen.findByText("Walk-forward History");
  vi.useFakeTimers();
  fireEvent.click(screen.getByRole("button", { name: "Run walk-forward" }));

  await act(async () => {});
  expect(runMock).toHaveBeenCalledTimes(1);
  expect(detailMock).not.toHaveBeenCalled();

  await act(async () => {
    vi.advanceTimersByTime(5000);
  });

  expect(detailMock).toHaveBeenCalledWith("9");
  expect(pushSpy).toHaveBeenCalledWith({}, "", "/walk-forwards/9");
  expect(popSpy).toHaveBeenCalled();
});

it("surfaces error_message and re-enables the button when polling reports failed", async () => {
  listMock.mockResolvedValue({ runs: [], total: 0, limit: 10, offset: 0 });
  runMock.mockResolvedValue({ walk_forward_run_id: 9 });
  detailMock.mockResolvedValue({
    ...runningDetail(9),
    run: {
      ...summary(9),
      status: "failed" as const,
      error_message: "boom",
      created_at: "2026-12-01T00:00:00"
    }
  });

  render(<WalkForwardListPage />);
  await screen.findByText("Walk-forward History");
  vi.useFakeTimers();
  fireEvent.click(screen.getByRole("button", { name: "Run walk-forward" }));
  await act(async () => {});

  await act(async () => {
    vi.advanceTimersByTime(5000);
  });

  expect(screen.getByText("boom")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Run walk-forward" })).toBeEnabled();
});

it("surfaces a 409 conflict without issuing a second POST", async () => {
  listMock.mockResolvedValue({ runs: [], total: 0, limit: 10, offset: 0 });
  runMock.mockRejectedValue(
    new ApiClientError("conflict", { kind: "http", status: 409, category: "operation_failed" })
  );

  render(<WalkForwardListPage />);
  await screen.findByText("Walk-forward History");
  fireEvent.click(screen.getByRole("button", { name: "Run walk-forward" }));

  expect(await screen.findByText(/already in progress/)).toBeInTheDocument();
  expect(runMock).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("button", { name: "Run walk-forward" })).toBeEnabled();
});

it("pauses polling while the document is hidden and resumes when visible", async () => {
  listMock.mockResolvedValue({ runs: [], total: 0, limit: 10, offset: 0 });
  runMock.mockResolvedValue({ walk_forward_run_id: 9 });
  detailMock.mockResolvedValue(runningDetail(9));

  render(<WalkForwardListPage />);
  await screen.findByText("Walk-forward History");
  vi.useFakeTimers();
  fireEvent.click(screen.getByRole("button", { name: "Run walk-forward" }));
  await act(async () => {});

  await act(async () => {
    vi.advanceTimersByTime(5000);
  });
  expect(detailMock).toHaveBeenCalledTimes(1);

  Object.defineProperty(document, "hidden", { configurable: true, value: true });
  await act(async () => {
    document.dispatchEvent(new Event("visibilitychange"));
    vi.advanceTimersByTime(15000);
  });
  expect(detailMock).toHaveBeenCalledTimes(1);

  Object.defineProperty(document, "hidden", { configurable: true, value: false });
  await act(async () => {
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await act(async () => {
    vi.advanceTimersByTime(5000);
  });
  expect(detailMock.mock.calls.length).toBeGreaterThanOrEqual(2);
});
