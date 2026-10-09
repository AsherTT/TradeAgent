import assert from "node:assert/strict";
import test from "node:test";
import { applicationModule, deferred, flush, mount } from "./component-harness.mjs";

const instrumentId = "11111111-1111-4111-8111-111111111111";
const runId = "22222222-2222-4222-8222-222222222222";
const company = { instrument_id: instrumentId, current_symbol: "TEST", company_name: "Synthetic company", exchange: "TEST", currency: "USD" };
const run = {
  research_run_id: runId, instrument_id: instrumentId, ticker: "TEST", query: "PRIVATE RESEARCH CONTENT",
  horizon: "3 days", requested_at: "2026-10-09T00:00:00Z", status: "pending", research_completion: null,
  collection_only: true, analysis_timestamp: null, research_budget: {}, budget_usage: {},
  data_quality_status: "UNVERIFIED", quality_gate_decision: null, progress_steps: [], failure_code: null,
  actual_cost_usd: null, quality_assessment: null,
};
const detail = { company, is_followed: false, research: { items: [run], total: 1, offset: 0, limit: 6 } };
const unauthorized = () => Response.json({ detail: "authentication_required" }, { status: 401 });
const report = { research_id: runId, ticker: "TEST", complete_analysis: false, citation_note: "", data_quality_status: "UNVERIFIED", quality_gate_decision: null, sections: [{ title: "Saved report", text: "PRIVATE SAVED REPORT", evidence_ids: [] }], citations: [], gaps: [], market_acquisition: null, financial_metric_assessments: [], catalyst_limitations: [] };

test("company follow 401 clears private research and rejects a late company poll", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const late = deferred();
  let reads = 0;
  const { CompanyWorkspace } = applicationModule("components/workspace/CompanyWorkspace");
  const page = await mount(t, CompanyWorkspace, { instrumentId }, async (_url, init) => {
    if (init?.method === "POST") return unauthorized();
    reads++;
    return reads === 1 ? Response.json(detail) : late.promise;
  });
  assert.ok(page.text().includes(run.query));
  await flush(() => t.mock.timers.tick(5000));
  await page.click("Follow company");
  assert.ok(page.navigations.includes("/login"));
  await flush(() => late.resolve(Response.json(detail)));
  assert.ok(!page.text().includes(run.query), "Expired private research was restored by an old read");
  await flush(() => t.mock.timers.tick(10000));
  assert.ok(!page.text().includes(run.query), "Expired private research was restored by an old read");
  assert.equal(reads, 2, "Expired session must not schedule new reads");
});

test("cancel 401 clears task and saved report while a report refresh is in flight", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const late = deferred();
  let reports = 0;
  const { ResearchRun } = applicationModule("components/research/ResearchRun");
  const page = await mount(t, ResearchRun, { runId, unavailable: false }, async (url) => {
    if (url.endsWith("/cancel")) return unauthorized();
    if (url.endsWith("/report")) {
      reports++;
      return reports === 1 ? Response.json(report) : late.promise;
    }
    return Response.json(run);
  });
  assert.ok(page.text().includes("PRIVATE SAVED REPORT"));
  await flush(() => t.mock.timers.tick(5000));
  await page.click("Cancel task");
  assert.ok(page.navigations.includes("/login"));
  await flush(() => late.resolve(Response.json(report)));
  assert.ok(!page.text().includes("PRIVATE SAVED REPORT"), "A late report survived cancellation's 401");
  assert.ok(!page.text().includes(run.query));
  await flush(() => t.mock.timers.tick(10000));
  assert.equal(reports, 2);
});

test("submit 401 clears research records and stops a late list from restoring the form", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const late = deferred();
  let lists = 0;
  let submittedQuery;
  const { ResearchWorkspace } = applicationModule("components/research/ResearchWorkspace");
  const page = await mount(t, ResearchWorkspace, { unavailable: false, initialCompany: instrumentId }, async (url, init) => {
    if (init?.method === "POST") { submittedQuery = JSON.parse(init.body).query; return unauthorized(); }
    if (url.endsWith("research/options")) return Response.json({ models_enabled: false });
    if (url.endsWith("research")) {
      lists++;
      return lists === 1 ? Response.json([run]) : late.promise;
    }
    if (url.includes(`companies/${instrumentId}`)) return Response.json(detail);
    return Response.json([company]);
  });
  await flush(() => t.mock.timers.tick(200));
  assert.ok(page.text().includes(run.query));
  await page.fill("#research-question", "PRIVATE QUESTION TO SUBMIT");
  await flush(() => t.mock.timers.tick(5000));
  await page.submit();
  assert.equal(submittedQuery, "PRIVATE QUESTION TO SUBMIT");
  assert.ok(page.navigations.includes("/login"));
  assert.ok(!page.text().includes(run.query), "Submission 401 left private records visible");
  await flush(() => late.resolve(Response.json([run])));
  assert.ok(!page.text().includes(run.query));
  assert.equal(page.document.querySelector("form"), null, "Expired session must not allow another submission");
  await flush(() => t.mock.timers.tick(10000));
  assert.equal(lists, 2);
});

test("a successful submission arriving after a list 401 cannot navigate to the expired account task", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const receipt = deferred();
  let lists = 0;
  let submittedQuery;
  const { ResearchWorkspace } = applicationModule("components/research/ResearchWorkspace");
  const page = await mount(t, ResearchWorkspace, { unavailable: false, initialCompany: instrumentId }, async (url, init) => {
    if (init?.method === "POST") { submittedQuery = JSON.parse(init.body).query; return receipt.promise; }
    if (url.endsWith("research/options")) return Response.json({ models_enabled: false });
    if (url.endsWith("research")) return ++lists === 1 ? Response.json([run]) : unauthorized();
    if (url.includes(`companies/${instrumentId}`)) return Response.json(detail);
    return Response.json([company]);
  });
  await flush(() => t.mock.timers.tick(200));
  await page.fill("#research-question", "PRIVATE QUESTION TO SUBMIT");
  await page.submit();
  assert.equal(submittedQuery, "PRIVATE QUESTION TO SUBMIT");
  await flush(() => t.mock.timers.tick(5000));
  assert.deepEqual(page.navigations, ["/login"]);
  await flush(() => receipt.resolve(Response.json({ research_run_id: runId }, { status: 202 })));
  assert.deepEqual(page.navigations, ["/login"], "Late success navigated back into an expired private task");
  await page.click("Retry");
  await flush(() => t.mock.timers.tick(10000));
  assert.equal(lists, 2, "Retry must not restart an expired session");
});

test("a late list 401 still expires the session when a sibling company read failed first", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const late = deferred();
  let lists = 0;
  let directories = 0;
  const { ResearchWorkspace } = applicationModule("components/research/ResearchWorkspace");
  const page = await mount(t, ResearchWorkspace, { unavailable: false, initialCompany: instrumentId }, async (url) => {
    if (url.endsWith("research/options")) return Response.json({ models_enabled: false });
    if (url.endsWith("research")) return ++lists === 1 ? Response.json([run]) : late.promise;
    if (url.includes(`companies/${instrumentId}`)) return Response.json(detail);
    return ++directories === 1 ? Response.json([company]) : Response.json({ detail: "backend_unavailable" }, { status: 503 });
  });
  await flush(() => t.mock.timers.tick(200));
  assert.ok(page.text().includes(run.query));
  await flush(() => t.mock.timers.tick(5000));
  await flush(() => late.resolve(unauthorized()));
  assert.deepEqual(page.navigations, ["/login"]);
  assert.ok(!page.text().includes(run.query));
  assert.equal(page.document.querySelector("form"), null);
});

test("successful company follow refreshes the actual status and preserves current research", async (t) => {
  const { CompanyWorkspace } = applicationModule("components/workspace/CompanyWorkspace");
  let followed = false;
  const page = await mount(t, CompanyWorkspace, { instrumentId }, async (_url, init) => {
    if (init?.method === "POST") { followed = true; return new Response(null, { status: 204 }); }
    return Response.json({ ...detail, is_followed: followed });
  });
  await page.click("Follow company");
  assert.ok(page.text().includes("Unfollow"));
  assert.ok(page.text().includes(run.query));
  assert.deepEqual(page.navigations, []);
});

test("successful cancellation loads the saved terminal task and report", async (t) => {
  const { ResearchRun } = applicationModule("components/research/ResearchRun");
  let cancelled = false;
  const page = await mount(t, ResearchRun, { runId, unavailable: false }, async (url) => {
    if (url.endsWith("/cancel")) { cancelled = true; return Response.json({ ...run, status: "cancelled" }); }
    if (url.endsWith("/report")) return Response.json(report);
    return Response.json({ ...run, status: cancelled ? "cancelled" : "pending" });
  });
  await page.click("Cancel task");
  assert.ok(page.text().includes("Cancelled"));
  assert.ok(page.text().includes("PRIVATE SAVED REPORT"));
  assert.ok(![...page.document.querySelectorAll("button")].some((button) => button.textContent === "Cancel task"));
  assert.deepEqual(page.navigations, []);
});

test("portal data navigation resolves to the existing scope notice in both languages", async (t) => {
  const { Workspace } = applicationModule("components/accounts/Workspace");
  for (const locale of ["zh", "en"]) {
    await t.test(locale, async (t) => {
      const page = await mount(t, Workspace, { account: { user_id: "synthetic", email: "fixture@example.test" }, unavailable: false }, async (url) => {
        if (url.includes("portal")) return Response.json({ watchlist: { items: [], total: 0, offset: 0, limit: 6 }, recent_research: { items: [], total: 0, offset: 0, limit: 6 }, active_research: [], active_research_total: 0 });
        return Response.json([]);
      }, locale);
      const label = locale === "zh" ? "数据说明" : "Data & sources";
      const link = [...page.document.querySelectorAll("a")].find((element) => element.textContent === label);
      assert.equal(link.getAttribute("href"), "/app#data-scope");
      assert.ok(page.document.getElementById("data-scope")?.textContent.includes(locale === "zh" ? "目录不是全市场行情" : "not a market-wide feed"));
    });
  }
});
