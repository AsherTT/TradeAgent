import assert from "node:assert/strict";
import test from "node:test";
import { applicationModule, deferred, flush, mount } from "./component-harness.mjs";

const instrumentId = "11111111-1111-4111-8111-111111111111";
const priorId = "22222222-2222-4222-8222-222222222222";
const latestId = "33333333-3333-4333-8333-333333333333";
const snapshot = {
  instrument_id: instrumentId, ticker: "TEST", query: "A private comparison question", horizon: "3-5 days",
  requested_at: "2026-10-08T00:00:00Z", analysis_timestamp: "2026-10-08T00:00:00Z",
  status: "insufficient_evidence", research_completion: "insufficient_evidence", collection_only: true,
  data_quality_status: "unverified", quality_gate_decision: "insufficient", qualified_evidence_count: 2, evidence_gap_count: 1,
};
const available = {
  availability: "available", window_limit: 50, has_more: false,
  latest: { ...snapshot, research_run_id: latestId },
  previous: { ...snapshot, research_run_id: priorId, analysis_timestamp: "2026-10-07T00:00:00Z", qualified_evidence_count: 1, evidence_gap_count: 2 },
  qualified_evidence_count_delta: 1, evidence_gap_count_delta: -1,
};
const detail = {
  company: { instrument_id: instrumentId, current_symbol: "TEST", company_name: "Offline company", exchange: "TEST", currency: "USD" },
  is_followed: false, directory_scope: "local_directory", research: { items: [], total: 0, offset: 0, limit: 6 },
  research_change: available,
};

test("company record change shows both stored cutoffs, signed coverage deltas and local report links", async (t) => {
  const { CompanyWorkspace } = applicationModule("components/workspace/CompanyWorkspace");
  const page = await mount(t, CompanyWorkspace, { instrumentId }, async () => Response.json(detail));
  const section = page.document.querySelector("#company-change");
  assert.ok(section, "Company must expose its actual research change section");
  assert.ok(section.textContent.includes("A private comparison question"));
  assert.ok(section.textContent.includes("+1"));
  assert.ok(section.textContent.includes("-1"));
  assert.ok(section.textContent.includes("not company performance"));
  assert.deepEqual([...section.querySelectorAll("time")].map((node) => node.dateTime), [snapshot.analysis_timestamp, "2026-10-07T00:00:00Z"]);
  assert.deepEqual([...section.querySelectorAll("a")].map((node) => node.getAttribute("href")), [`/app/research/${latestId}`, `/app/research/${priorId}`]);
  assert.equal(page.document.querySelector('nav a[href="#company-change"]')?.textContent, "Research record changes");
});

test("unknown changes stay unavailable in Chinese and disclose the bounded window", async (t) => {
  const { CompanyWorkspace } = applicationModule("components/workspace/CompanyWorkspace");
  const page = await mount(t, CompanyWorkspace, { instrumentId }, async () => Response.json({
    ...detail, research_change: { ...available, availability: "no_comparable_previous", previous: null,
      has_more: true, qualified_evidence_count_delta: null, evidence_gap_count_delta: null },
  }), "zh");
  const section = page.document.querySelector("#company-change");
  assert.ok(section.textContent.includes("暂不能计算变化"));
  assert.ok(section.textContent.includes("未作全历史比较"));
  assert.ok(section.textContent.includes("不代表公司表现"));
  assert.equal(section.querySelectorAll("article").length, 1);
  assert.ok(!section.textContent.includes("与上次相比"), "Unknown must not render an invented zero change");
});

test("a company without finished research shows no synthetic comparison or report links", async (t) => {
  const { CompanyWorkspace } = applicationModule("components/workspace/CompanyWorkspace");
  const page = await mount(t, CompanyWorkspace, { instrumentId }, async () => Response.json({
    ...detail, research_change: { ...available, availability: "no_finished_research", latest: null, previous: null,
      qualified_evidence_count_delta: null, evidence_gap_count_delta: null },
  }));
  const section = page.document.querySelector("#company-change");
  assert.ok(section.textContent.includes("No finished research"));
  assert.equal(section.querySelectorAll("article, a").length, 0);
  assert.ok(!section.textContent.includes(snapshot.query));
});

test("follow session expiry clears the comparison and cannot restore it from a late company read", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const late = deferred();
  let reads = 0;
  const { CompanyWorkspace } = applicationModule("components/workspace/CompanyWorkspace");
  const page = await mount(t, CompanyWorkspace, { instrumentId }, async (_url, init) => {
    if (init?.method === "POST") return Response.json({ detail: "authentication_required" }, { status: 401 });
    return ++reads === 1 ? Response.json({ ...detail, research: { ...detail.research, items: [{ ...snapshot, research_run_id: latestId, status: "running" }] } }) : late.promise;
  });
  assert.ok(page.text().includes(snapshot.query));
  await flush(() => t.mock.timers.tick(5000));
  await page.click("Follow company");
  assert.deepEqual(page.navigations, ["/login"]);
  await flush(() => late.resolve(Response.json(detail)));
  assert.equal(page.document.querySelector("#company-change"), null);
  assert.ok(!page.text().includes(snapshot.query));
});
