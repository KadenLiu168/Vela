import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiClientError } from "../api/client";

/** The states a read can be in when the resource itself always exists. */
export type LoadableResourceState<T> =
  | { status: "loading"; data?: never; error?: never }
  | { status: "ready"; data: T; error?: never }
  | { status: "error"; data?: never; error: unknown };

type NotFound = { status: "not-found"; data?: never; error?: never };

/** A read of an entity that can be missing, so the page also renders
 *  `not-found`. A page that does not declare `hasNotFoundState` never produces
 *  that state and should not have to handle one it cannot reach. */
export type ResourceState<T> = LoadableResourceState<T> | NotFound;

type StoredState<T, K> =
  | { status: "loading"; key?: never; data?: never; error?: never }
  | { status: "ready"; key: K; data: T; error?: never }
  | { status: "not-found"; key: K; data?: never; error?: never }
  | { status: "error"; key: K; data?: never; error: unknown };

type UseResourceOptions<T, K> = {
  /** True when this resource's 404 is a state the page renders, such as a
   *  detail page for an id that does not exist. A list endpoint has no such
   *  state, so its 404 stays an ordinary failure. */
  hasNotFoundState?: boolean;
  /** Identifies the request. Changing it starts a new load, and the previous
   *  request's result is never reported against the new one. */
  key: K;
  load: () => Promise<T>;
};

/**
 * Owns one read's lifecycle: which request is in flight, which result belongs
 * to which request, and how a retry returns to the loading state.
 *
 * The state and the request key are held together on purpose. Every page that
 * reads data has to answer "is this result for the request I am showing now?",
 * and holding the two apart turns that answer into two sources of truth that
 * must be kept in step by hand.
 */
export function useResource<T, K extends string | number>(options: {
  hasNotFoundState: true;
  key: K;
  load: () => Promise<T>;
}): { state: ResourceState<T>; reload: () => void };
export function useResource<T, K extends string | number>(options: {
  hasNotFoundState?: false;
  key: K;
  load: () => Promise<T>;
}): { state: LoadableResourceState<T>; reload: () => void };
export function useResource<T, K extends string | number>({
  hasNotFoundState = false,
  key,
  load
}: UseResourceOptions<T, K>): { state: ResourceState<T>; reload: () => void } {
  const [stored, setStored] = useState<StoredState<T, K>>({ status: "loading" });
  const [reloadCount, setReloadCount] = useState(0);

  // The loader is a fresh closure on every render; keeping the latest one in a
  // ref lets the effect depend only on the request key.
  const loadRef = useRef(load);
  useEffect(() => {
    loadRef.current = load;
  });

  useEffect(() => {
    let isCurrent = true;

    loadRef
      .current()
      .then((data) => {
        if (isCurrent) {
          setStored({ status: "ready", key, data });
        }
      })
      .catch((error: unknown) => {
        if (!isCurrent) {
          return;
        }

        if (hasNotFoundState && error instanceof ApiClientError && error.status === 404) {
          setStored({ status: "not-found", key });
          return;
        }

        setStored({ status: "error", key, error });
      });

    return () => {
      isCurrent = false;
    };
  }, [hasNotFoundState, key, reloadCount]);

  const reload = useCallback(() => {
    setStored({ status: "loading" });
    setReloadCount((value) => value + 1);
  }, []);

  // Memoized so the returned state keeps its identity while the stored result
  // and the key are unchanged. Pages that derive an effect from this state —
  // as BacktestDetailPage's tab-gated second read does — would otherwise re-run
  // that effect on every render.
  const state = useMemo(() => describe(stored, key), [stored, key]);

  return { state, reload };
}

function describe<T, K>(stored: StoredState<T, K>, key: K): ResourceState<T> {
  if (stored.status === "loading" || stored.key !== key) {
    return { status: "loading" };
  }

  if (stored.status === "ready") {
    return { status: "ready", data: stored.data };
  }

  if (stored.status === "not-found") {
    return { status: "not-found" };
  }

  return { status: "error", error: stored.error };
}
