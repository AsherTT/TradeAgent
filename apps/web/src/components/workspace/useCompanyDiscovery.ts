"use client";

import { useEffect, useRef, useState } from "react";
import { ResearchApiError, researchRequest } from "@/components/research/api";

// Keep requests abortable and response publication tied to the current query/identity.
export function useCompanyDiscovery<T>(path: string, enabled: boolean, revision: number) {
  const key = `${path}:${revision}`;
  const [request, setRequest] = useState({ key, enabled, generation: 0 });
  const matchesRequest = request.key === key && request.enabled === enabled;
  // Track transitions, including A -> B -> A, before rendering any prior response.
  if (!matchesRequest) setRequest({ key, enabled, generation: request.generation + 1 });
  const generation = request.generation;
  const [expired, setExpired] = useState(false);
  const mounted = useRef(false);
  const [result, setResult] = useState<{ generation: number; data: T | null; error: string | null } | null>(null);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  useEffect(() => {
    if (!enabled || expired) return;
    const controller = new AbortController();
    let disposed = false;
    const timer = window.setTimeout(() => {
      void researchRequest<T>(path, { signal: controller.signal }).then((data) => {
        if (!disposed) setResult({ generation, data, error: null });
      }).catch((error: unknown) => {
        const unauthorized = error instanceof ResearchApiError && error.status === 401;
        // Even an earlier query's 401 revokes this mounted account view.
        if (unauthorized && mounted.current) setExpired(true);
        if (disposed) return;
        const code = error instanceof ResearchApiError ? error.code : "backend_unavailable";
        setResult({ generation, data: null, error: unauthorized ? "session_required" : code });
      });
    }, 200);
    return () => { disposed = true; window.clearTimeout(timer); controller.abort(); };
  }, [path, generation, enabled, expired]);
  if (expired) return { data: null, error: "session_required", pending: false };
  const current = enabled && matchesRequest && result?.generation === generation ? result : null;
  return { data: current?.data ?? null, error: current?.error ?? null, pending: enabled && !current };
}
