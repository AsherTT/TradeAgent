import type { Company } from "@/components/research/contracts";
import type { PortalSummary } from "./contracts";

/** Stop invalidates even reads whose transport ignores AbortSignal. */
export function startWorkspacePolling({ load, onUpdate, onFailure }: {
  load: (signal: AbortSignal) => Promise<[PortalSummary, Company[]]>;
  onUpdate: (result: [PortalSummary, Company[]]) => boolean;
  onFailure: (failure: unknown) => void;
}) {
  const controller = new AbortController();
  let active = true;
  let timer: ReturnType<typeof setTimeout>;
  function stop() {
    active = false;
    clearTimeout(timer);
    controller.abort();
  }
  async function poll() {
    try {
      const result = await load(controller.signal);
      if (!active) return;
      if (onUpdate(result) && active) timer = setTimeout(() => void poll(), 5000);
    } catch (failure) {
      if (!active) return;
      stop();
      onFailure(failure);
    }
  }
  timer = setTimeout(() => void poll(), 200);
  return stop;
}
