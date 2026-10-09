import assert from "node:assert/strict";
import test from "node:test";
import { applicationModule, deferred, flush, mount } from "./component-harness.mjs";

const instrumentId = "11111111-1111-4111-8111-111111111111";
const company = { instrument_id: instrumentId, current_symbol: "TEST", company_name: "Synthetic company", exchange: "TEST", currency: "USD" };
const latest = {
  research_run_id: "22222222-2222-4222-8222-222222222222", instrument_id: instrumentId,
  ticker: "TEST", query: "PRIVATE COMPARISON", horizon: "3-5 days", collection_only: true,
  requested_at: "2026-10-08T00:00:00Z", analysis_timestamp: "2026-10-08T00:00:00Z",
  status: "insufficient_evidence", research_completion: "insufficient_evidence",
  data_quality_status: "unverified", quality_gate_decision: null,
  qualified_evidence_count: 2, evidence_gap_count: 1,
};
const change = {
  availability: "available", window_limit: 50, has_more: true, latest,
  previous: { ...latest, research_run_id: "33333333-3333-4333-8333-333333333333", analysis_timestamp: "2026-10-07T00:00:00Z" },
  qualified_evidence_count_delta: 1, evidence_gap_count_delta: -1,
};
const portal = {
  directory_scope: "local_directory", watchlist: {items:[company], total:1, offset:0, limit:6},
  recent_research: {items:[], total:0, offset:0, limit:6}, active_research:[], active_research_total:0,
  research_changes: [{instrument_id:instrumentId, research_change:change}],
};

test("portal exposes bounded watchlist comparison, both cutoffs and local report links", async (t) => {
  t.mock.timers.enable({apis:["setTimeout"]});
  const { Workspace } = applicationModule("components/accounts/Workspace");
  const page = await mount(t, Workspace, {account:null, unavailable:false}, async url => Response.json(url.includes("/portal?") ? portal : [company]));
  await flush(() => t.mock.timers.tick(200));
  const summaries = page.document.querySelectorAll('[aria-label="Research record changes"]');
  assert.equal(summaries.length, 1, "Directory must not duplicate the private comparison");
  const summary = summaries[0];
  assert.ok(summary.textContent.includes("+1") && summary.textContent.includes("-1"));
  assert.ok(summary.textContent.includes("50") && summary.textContent.includes("not company performance"));
  assert.ok(summary.textContent.includes("Older records"));
  assert.deepEqual([...summary.querySelectorAll("time")].map(node => node.dateTime), [latest.analysis_timestamp, change.previous.analysis_timestamp]);
  assert.deepEqual([...summary.querySelectorAll("a")].map(node => node.getAttribute("href")), [
    `/app/research/${latest.research_run_id}`, `/app/research/${change.previous.research_run_id}`,
    `/app/companies/${instrumentId}#company-change`,
  ]);
});

test("Chinese unknown history and legacy missing field never manufacture zero changes", async (t) => {
  t.mock.timers.enable({apis:["setTimeout"]});
  const { Workspace } = applicationModule("components/accounts/Workspace");
  let snapshot = {...portal, research_changes:[{instrument_id:instrumentId, research_change:{
    ...change, availability:"no_comparable_previous", previous:null,
    qualified_evidence_count_delta:null, evidence_gap_count_delta:null,
  }}]};
  const page = await mount(t, Workspace, {account:null, unavailable:false}, async url => Response.json(url.includes("/portal?") ? snapshot : []), "zh");
  await flush(() => t.mock.timers.tick(200));
  let summary = page.document.querySelector('[aria-label="研究记录变化"]');
  assert.ok(summary.textContent.includes("暂无相同条件"));
  assert.ok(!summary.textContent.includes("证据数变化"));
  assert.equal(summary.querySelectorAll("time").length, 1);
  snapshot = {...portal, research_changes:[{instrument_id:instrumentId, research_change:{
    ...change, availability:"no_finished_research", latest:null, previous:null,
    qualified_evidence_count_delta:null, evidence_gap_count_delta:null,
  }}]};
  await page.click("刷新");
  await flush(() => t.mock.timers.tick(200));
  summary = page.document.querySelector('[aria-label="研究记录变化"]');
  assert.ok(summary.textContent.includes("尚无有效分析时间"));
  assert.equal(summary.querySelectorAll("time").length, 0);
  assert.equal(summary.querySelectorAll('a[href^="/app/research/"]').length, 0);
  snapshot = {...portal, research_changes:undefined};
  await page.click("刷新");
  await flush(() => t.mock.timers.tick(200));
  summary = page.document.querySelector('[aria-label="研究记录变化"]');
  assert.ok(summary.textContent.includes("暂不可用"));
  assert.ok(!summary.textContent.includes("尚无有效分析时间"));
});

test("watchlist paging hides old comparisons until the new page arrives and preserves search on language change", async (t) => {
  t.mock.timers.enable({apis:["setTimeout"]});
  const next = deferred();
  const other = {...company, instrument_id:"44444444-4444-4444-8444-444444444444", current_symbol:"OTHER"};
  const snapshot = {...portal, watchlist:{...portal.watchlist, total:7}};
  const { Workspace } = applicationModule("components/accounts/Workspace");
  const page = await mount(t, Workspace, {account:null, unavailable:false}, async url => {
    if (url.includes("watchlist_offset=6")) return next.promise;
    return Response.json(url.includes("/portal?") ? snapshot : []);
  });
  await flush(() => t.mock.timers.tick(200));
  await page.fill("#company-search", "Keep this search");
  await flush(() => t.mock.timers.tick(200));
  await page.click("中文");
  assert.equal(page.document.querySelector("#company-search").value, "Keep this search");
  assert.equal(page.document.querySelectorAll('[aria-label="研究记录变化"]').length, 1);
  await page.click("下一页");
  assert.equal(page.document.querySelectorAll('[aria-label="研究记录变化"]').length, 0);
  await flush(() => t.mock.timers.tick(200));
  await flush(() => next.resolve(Response.json({
    ...snapshot, watchlist:{items:[other], total:7, offset:6, limit:6},
    research_changes:[{instrument_id:other.instrument_id, research_change:{
      ...change, availability:"no_finished_research", latest:null, previous:null,
      qualified_evidence_count_delta:null, evidence_gap_count_delta:null,
    }}],
  })));
  const summary = page.document.querySelector('[aria-label="研究记录变化"]');
  assert.equal(summary.querySelector("a").getAttribute("href"), `/app/companies/${other.instrument_id}#company-change`);
  assert.equal(summary.querySelectorAll("time").length, 0);
});

test("follow 401 clears portal changes and a late poll cannot restore them", async (t) => {
  t.mock.timers.enable({apis:["setTimeout"]});
  const late = deferred();
  let reads = 0;
  const { Workspace } = applicationModule("components/accounts/Workspace");
  const snapshot = {...portal, active_research_total:1};
  const page = await mount(t, Workspace, {account:null, unavailable:false}, async (url, init) => {
    if (init?.method === "DELETE") return Response.json({detail:"authentication_required"}, {status:401});
    if (url.includes("/portal?")) return ++reads === 1 ? Response.json(snapshot) : late.promise;
    return Response.json([]);
  });
  await flush(() => t.mock.timers.tick(200));
  assert.ok(page.document.querySelector('[aria-label="Research record changes"]'));
  await flush(() => t.mock.timers.tick(5000));
  await page.click("Unfollow");
  assert.deepEqual(page.navigations, ["/login"]);
  await flush(() => late.resolve(Response.json(snapshot)));
  assert.equal(page.document.querySelector('[aria-label="Research record changes"]'), null);
  assert.equal(page.document.querySelector('a[href$="#company-change"]'), null);
});
