import { backendUrl } from "@/lib/account-api";

function jsonResponse(body: unknown, init?: ResponseInit) {
  const headers = new Headers(init?.headers);
  headers.set("Cache-Control", "no-store");
  return Response.json(body, { ...init, headers });
}

async function boundedBody(request: Request, limit: number): Promise<string | null> {
  const reader = request.body?.getReader();
  if (!reader) return "";
  const decoder = new TextDecoder();
  let size = 0;
  let body = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) { await reader.cancel(); return null; }
      body += decoder.decode(value, { stream: true });
    }
    return body + decoder.decode();
  } finally { reader.releaseLock(); }
}

const exactRoutes: Record<string, string[]> = {
  "auth/register": ["POST"], "auth/login": ["POST"],
  "auth/logout": ["POST"], "auth/me": ["GET"],
  "workspace/research": ["GET", "POST"], "workspace/research/options": ["GET"],
  "workspace/companies": ["GET"], "workspace/watchlist": ["GET"], "workspace/portal": ["GET"],
};

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const path = (await context.params).path.join("/");
  const researchRoute = /^workspace\/research\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?:\/(report|cancel))?$/i.exec(path);
  const companyRoute = /^workspace\/companies\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(path);
  const methods = exactRoutes[path] ?? (
    companyRoute ? ["GET"] : /^workspace\/watchlist\/[0-9a-f-]{36}$/i.test(path) ? ["POST", "DELETE"] : []
  );
  if (researchRoute) methods.push(researchRoute[1] === "cancel" ? "POST" : "GET");
  if (!methods.includes(request.method)) return jsonResponse({ detail: "not_found" }, { status: 404 });
  const origin = request.headers.get("origin");
  const allowedOrigins = process.env.TRADEAGENT_APP_ORIGIN
    ? [process.env.TRADEAGENT_APP_ORIGIN]
    : ["http://127.0.0.1:3107", "http://localhost:3107"];
  if (request.method !== "GET" && (!origin || !allowedOrigins.includes(origin))) {
    return jsonResponse({ detail: "origin_not_allowed" }, { status: 403 });
  }
  const headers = new Headers();
  headers.set("Accept", "application/json");
  if (origin) headers.set("Origin", origin);
  const token = request.headers.get("cookie")?.split(";")
    .map((part) => part.trim()).find((part) => part.startsWith("tradeagent_session="));
  if (token) headers.set("Cookie", token);
  let body: string | undefined;
  if (request.method === "POST" && (path === "workspace/research" || (path !== "auth/logout" && path.startsWith("auth/")))) {
    const sizeLimit = path === "workspace/research" ? 8192 : 4096;
    const inputError = path === "workspace/research" ? "invalid_research_input" : "invalid_auth_input";
    if (!request.headers.get("content-type")?.startsWith("application/json")) {
      return jsonResponse({ detail: inputError }, { status: 415 });
    }
    if (Number(request.headers.get("content-length") ?? 0) > sizeLimit) {
      return jsonResponse({ detail: inputError }, { status: 413 });
    }
    const bounded = await boundedBody(request, sizeLimit);
    if (bounded === null) {
      return jsonResponse({ detail: inputError }, { status: 413 });
    }
    body = bounded;
    headers.set("Content-Type", "application/json");
  }
  try {
    const target = backendUrl(`/${path}`);
    if (path === "workspace/companies") {
      const query = new URL(request.url).searchParams.get("query");
      if (query !== null) target.searchParams.set("query", query);
    }
    if (path === "workspace/portal" || companyRoute) {
      const params = new URL(request.url).searchParams;
      const keys = path === "workspace/portal" ? ["limit", "watchlist_offset", "research_offset"] : ["limit", "research_offset"];
      for (const key of keys) {
        const value = params.get(key);
        if (value !== null) target.searchParams.set(key, value);
      }
    }
    const upstream = await fetch(target, {
      method: request.method, headers, body, cache: "no-store",
      signal: AbortSignal.timeout(10000), redirect: "error",
    });
    if (upstream.status >= 500) {
      return jsonResponse({ detail: "backend_unavailable" }, { status: 503, headers: { "Cache-Control": "no-store" } });
    }
    const resultHeaders = new Headers({ "Cache-Control": "no-store" });
    resultHeaders.set("Content-Type", "application/json");
    for (const cookie of upstream.headers.getSetCookie()) resultHeaders.append("Set-Cookie", cookie);
    const retry = upstream.headers.get("Retry-After");
    if (retry) resultHeaders.set("Retry-After", retry);
    return new Response(upstream.status === 204 ? null : await upstream.text(), {
      status: upstream.status, headers: resultHeaders,
    });
  } catch {
    return jsonResponse({ detail: "backend_unavailable" }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}

export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
