import { readApiError } from "@/components/accounts/copy";

export class ResearchApiError extends Error {
  constructor(public code: string, public status: number) { super(code); }
}
export async function researchRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend/workspace/${path}`, {
      ...init, cache: "no-store", signal: init?.signal ? AbortSignal.any([init.signal, AbortSignal.timeout(12000)]) : AbortSignal.timeout(12000),
    });
  } catch (error) {
    if (init?.signal?.aborted) throw error;
    throw new ResearchApiError("backend_unavailable", 503);
  }
  if (!response.ok) throw new ResearchApiError(await readApiError(response), response.status);
  try { return await response.json() as T; }
  catch { throw new ResearchApiError("backend_unavailable", 503); }
}
