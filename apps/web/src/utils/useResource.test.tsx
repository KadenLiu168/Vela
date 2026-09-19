import { act, renderHook, waitFor } from "@testing-library/react";
import { StrictMode, type ReactNode } from "react";
import { expect, it, vi } from "vitest";
import { ApiClientError } from "../api/client";
import { useResource } from "./useResource";

function Strict({ children }: { children: ReactNode }) {
  return <StrictMode>{children}</StrictMode>;
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
}

it("reports loading, then the loaded data", async () => {
  const load = vi.fn().mockResolvedValue({ id: 7 });

  const { result } = renderHook(() => useResource({ key: 7, load }));

  expect(result.current.state.status).toBe("loading");

  await waitFor(() => expect(result.current.state.status).toBe("ready"));
  expect(result.current.state.data).toEqual({ id: 7 });
});

it("reports loading immediately when the key changes, without showing the previous data", async () => {
  const { result, rerender } = renderHook(
    ({ key }) => useResource({ key, load: () => Promise.resolve({ id: key }) }),
    { initialProps: { key: 1 } }
  );

  await waitFor(() => expect(result.current.state.status).toBe("ready"));
  expect(result.current.state.data).toEqual({ id: 1 });

  rerender({ key: 2 });

  expect(result.current.state.status).toBe("loading");
  await waitFor(() => expect(result.current.state.data).toEqual({ id: 2 }));
});

it("does not let a stale response overwrite the current request's result", async () => {
  const slow = deferred<{ id: number }>();
  const { result, rerender } = renderHook(
    ({ key }) =>
      useResource({ key, load: () => (key === 1 ? slow.promise : Promise.resolve({ id: key })) }),
    { initialProps: { key: 1 } }
  );

  rerender({ key: 2 });
  await waitFor(() => expect(result.current.state.data).toEqual({ id: 2 }));

  await act(async () => {
    slow.resolve({ id: 1 });
  });

  expect(result.current.state.data).toEqual({ id: 2 });
});

it("maps a 404 to not-found only when the page declares that state", async () => {
  const notFound = new ApiClientError("gone", { kind: "http", status: 404, category: "not_found" });

  const withState = renderHook(() =>
    useResource({ hasNotFoundState: true, key: 1, load: () => Promise.reject(notFound) })
  );
  await waitFor(() => expect(withState.result.current.state.status).toBe("not-found"));

  const withoutState = renderHook(() =>
    useResource({ key: 1, load: () => Promise.reject(notFound) })
  );
  await waitFor(() => expect(withoutState.result.current.state.status).toBe("error"));
});

it("reports a non-404 failure as an error carrying the failure", async () => {
  const failure = new ApiClientError("boom", { kind: "http", status: 500, category: "unexpected" });

  const { result } = renderHook(() => useResource({ key: 1, load: () => Promise.reject(failure) }));

  await waitFor(() => expect(result.current.state.status).toBe("error"));
  expect(result.current.state.error).toBe(failure);
});

it("returns to loading on reload and settles on the new result", async () => {
  const load = vi
    .fn()
    .mockRejectedValueOnce(new ApiClientError("offline", { kind: "network" }))
    .mockResolvedValueOnce({ id: 7 });
  const { result } = renderHook(() => useResource({ key: 7, load }));

  await waitFor(() => expect(result.current.state.status).toBe("error"));

  act(() => {
    result.current.reload();
  });

  expect(result.current.state.status).toBe("loading");
  await waitFor(() => expect(result.current.state.status).toBe("ready"));
  expect(load).toHaveBeenCalledTimes(2);
});

it("does not write state after unmount", async () => {
  const pending = deferred<{ id: number }>();
  const errors = vi.spyOn(console, "error").mockImplementation(() => undefined);

  const { unmount } = renderHook(() => useResource({ key: 1, load: () => pending.promise }));
  unmount();

  await act(async () => {
    pending.resolve({ id: 1 });
  });

  expect(errors).not.toHaveBeenCalled();
  errors.mockRestore();
});

it("uses the latest loader without refetching on every render", async () => {
  const load = vi.fn((label: string) => Promise.resolve({ label }));
  const { result, rerender } = renderHook(({ label }) => useResource({ key: 1, load: () => load(label) }), {
    initialProps: { label: "first" }
  });

  await waitFor(() => expect(result.current.state.status).toBe("ready"));

  rerender({ label: "second" });

  expect(load).toHaveBeenCalledTimes(1);
  expect(result.current.state.data).toEqual({ label: "first" });
});

it("keeps its state sound when the mount's effects run twice", async () => {
  const load = vi.fn(() => Promise.resolve({ id: 7 }));

  const { result } = renderHook(() => useResource({ key: 7, load }), { wrapper: Strict });

  await waitFor(() => expect(result.current.state.status).toBe("ready"));
  expect(result.current.state.data).toEqual({ id: 7 });
});

it("fetches once for a single mount outside StrictMode", async () => {
  const load = vi.fn(() => Promise.resolve({ id: 7 }));

  const { result } = renderHook(() => useResource({ key: 7, load }));

  await waitFor(() => expect(result.current.state.status).toBe("ready"));
  expect(load).toHaveBeenCalledTimes(1);
});

it("keeps the returned state's identity while the result is unchanged", async () => {
  const load = vi.fn(() => Promise.resolve({ id: 7 }));
  const { result, rerender } = renderHook(({ tick }) => {
    void tick;
    return useResource({ key: 7, load });
  }, { initialProps: { tick: 1 } });

  await waitFor(() => expect(result.current.state.status).toBe("ready"));
  const first = result.current.state;

  rerender({ tick: 2 });

  expect(result.current.state).toBe(first);
});
