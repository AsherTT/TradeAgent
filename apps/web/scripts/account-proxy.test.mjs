import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { runInNewContext } from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../src/app/api/backend/[...path]/route.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;

function handler(fetch, env = {}) {
  const compiledModule = { exports: {} };
  runInNewContext(compiled, {
    module: compiledModule, exports: compiledModule.exports, fetch, Request, Response, Headers, URL, TextEncoder, TextDecoder, AbortSignal,
    process: { env },
    require: () => ({ backendUrl: (path) => new URL(path, "http://127.0.0.1:8000") }),
  });
  return compiledModule.exports;
}
function context(path) { return { params: Promise.resolve({ path: path.split("/") }) }; }
function loginRequest(origin = "http://127.0.0.1:3107", body = "{}") {
  // Next may normalize request.url to localhost even when the browser uses 127.0.0.1.
  return new Request("http://localhost:3107/api/backend/auth/login", {
    method: "POST", headers: { Origin: origin, "Content-Type": "application/json" }, body,
  });
}

test("both configured loopback origins can log in despite Next URL normalization", async () => {
  const routes = handler(async () => Response.json({ email: "local@example.test" }));
  for (const origin of ["http://127.0.0.1:3107", "http://localhost:3107"]) {
    assert.equal((await routes.POST(loginRequest(origin), context("auth/login"))).status, 200);
  }
});
test("untrusted origins and unexposed internal research routes never reach the backend", async () => {
  let requests = 0;
  const routes = handler(async () => { requests++; return Response.json({}); });
  assert.equal((await routes.POST(loginRequest("https://untrusted.example"), context("auth/login"))).status, 403);
  assert.equal((await routes.GET(new Request("http://localhost:3107/api/backend/research"), context("research"))).status, 404);
  assert.equal(requests, 0);
});
test("network failures and database server errors become safe unavailable responses", async () => {
  for (const fetch of [async () => { throw new Error("private infrastructure detail"); },
    async () => new Response("private database failure", { status: 500 })]) {
    const response = await handler(fetch).POST(loginRequest(), context("auth/login"));
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), { detail: "backend_unavailable" });
  }
});
test("only the account cookie is forwarded and the HttpOnly session header is preserved", async () => {
  let cookie;
  const routes = handler(async (_url, options) => {
    cookie = options.headers.get("cookie");
    return Response.json({ email: "local@example.test" }, { headers: {
      "Set-Cookie": "tradeagent_session=test-session; Path=/; HttpOnly; SameSite=Lax",
    } });
  });
  const response = await routes.GET(new Request("http://localhost:3107/api/backend/auth/me", {
    headers: { Cookie: "language=zh; tradeagent_session=test-session; unrelated=private" },
  }), context("auth/me"));
  assert.equal(cookie, "tradeagent_session=test-session");
  assert.match(response.headers.get("set-cookie"), /HttpOnly/);
  assert.equal(response.headers.get("cache-control"), "no-store");
});
test("credential size limits and configured cloud origin are enforced", async () => {
  const routes = handler(async () => Response.json({}), { TRADEAGENT_APP_ORIGIN: "https://tradeagent.example" });
  assert.equal((await routes.POST(loginRequest(), context("auth/login"))).status, 403);
  assert.equal((await routes.POST(loginRequest("https://tradeagent.example"), context("auth/login"))).status, 200);
  assert.equal((await routes.POST(loginRequest("https://tradeagent.example", "x".repeat(4097)), context("auth/login"))).status, 413);
});

test("research submission forwards bounded JSON and exposes only protected methods", async () => {
  const calls = [];
  const routes = handler(async (url, options) => { calls.push({ url, options }); return Response.json({ research_run_id: "run" }, { status: 202 }); });
  const request = new Request("http://localhost:3107/api/backend/workspace/research?unexpected=1", {
    method: "POST", headers: { Origin: "http://127.0.0.1:3107", "Content-Type": "application/json", Cookie: "tradeagent_session=test" }, body: '{"query":"Evidence"}',
  });
  const response = await routes.POST(request, context("workspace/research"));
  assert.equal(response.status, 202);
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.equal(calls[0].options.body, '{"query":"Evidence"}');
  assert.equal(calls[0].options.headers.get("content-type"), "application/json");
  assert.equal(calls[0].url.search, "");
  const id = "ddc0c29b-6c1e-43c7-9f37-8a6e43a481ad";
  for (const path of [`workspace/research/${id}`, `workspace/research/${id}/report`, "workspace/research/options"]) {
    assert.equal((await routes.GET(new Request(`http://localhost:3107/api/backend/${path}`), context(path))).status, 202);
    assert.equal((await routes.POST(request, context(path))).status, 404);
  }
  const cancel = new Request("http://localhost:3107/", { method: "POST", headers: { Origin: "http://127.0.0.1:3107" } });
  assert.equal((await routes.POST(cancel, context(`workspace/research/${id}/cancel`))).status, 202);
  for (const path of [`workspace/research/${id}/theses`, "workspace/research/bad-id", `research/${id}/report`, "rag/documents"]) {
    assert.equal((await routes.GET(new Request("http://localhost:3107/"), context(path))).status, 404);
  }
});
test("oversized research JSON and missing origins are rejected before dispatch", async () => {
  const routes = handler(async () => { assert.fail("request should be rejected before forwarding"); });
  const oversized = new Request("http://localhost:3107/", { method: "POST", headers: {
    Origin: "http://127.0.0.1:3107", "Content-Type": "application/json",
  }, body: "x".repeat(8193) });
  assert.equal((await routes.POST(oversized, context("workspace/research"))).status, 413);
  const missing = new Request("http://localhost:3107/", { method: "POST" });
  assert.equal((await routes.POST(missing, context("workspace/research"))).status, 403);
});

test("company search forwards its query without unrelated browser parameters", async () => {
  let target;
  const routes = handler(async (url) => { target = url; return Response.json([]); });
  const response = await routes.GET(new Request("http://localhost:3107/api/backend/workspace/companies?query=KLAC&user_id=private&limit=999"), context("workspace/companies"));
  assert.equal(response.status, 200);
  assert.equal(target.search, "?query=KLAC");
});

test("portal and company detail expose only GET with their bounded query parameter names", async () => {
  const targets = [];
  const routes = handler(async (url) => { targets.push(url); return Response.json({}); });
  const id = "ddc0c29b-6c1e-43c7-9f37-8a6e43a481ad";
  const query = "?limit=1&research_offset=2&watchlist_offset=1&user_id=someone&query=secret";
  for (const path of ["workspace/portal", `workspace/companies/${id}`]) {
    const response = await routes.GET(new Request(`http://localhost:3107/api/backend/${path}${query}`), context(path));
    assert.equal(response.status, 200);
    const target = targets.at(-1);
    assert.equal(target.searchParams.get("limit"), "1");
    assert.equal(target.searchParams.get("research_offset"), "2");
    assert.equal(target.searchParams.has("user_id"), false);
    assert.equal(target.searchParams.has("query"), false);
    assert.equal(target.searchParams.get("watchlist_offset"), path === "workspace/portal" ? "1" : null);
    assert.equal((await routes.POST(loginRequest(), context(path))).status, 404);
  }
  const before = targets.length;
  for (const path of ["workspace/companies/not-a-uuid", `workspace/companies/${id}/research`, "workspace/portal/admin"]) {
    assert.equal((await routes.GET(new Request("http://localhost:3107/"), context(path))).status, 404);
  }
  assert.equal(targets.length, before);
});
