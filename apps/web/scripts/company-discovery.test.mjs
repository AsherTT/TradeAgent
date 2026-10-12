import assert from "node:assert/strict";
import { test } from "node:test";
import { setTimeout } from "node:timers/promises";
import { applicationModule, deferred, flush, mount } from "./component-harness.mjs";

const { CompanyDiscoverySearch } = applicationModule("components/workspace/CompanyDiscoverySearch");
const id = "ddc0c29b-6c1e-43c7-9f37-8a6e43a481ad";
const metadata = { source: "sec_company_tickers_exchange", source_url: "https://www.sec.gov/files/company_tickers_exchange.json", fetched_at: "2026-10-12T08:00:00Z", stale: false, directory_total: 10445 };
const items = [
  { cik: "0000320193", name: "Apple Inc.", symbol: "AAPL", exchange: "NASDAQ", instrument_id: null },
  { cik: "0000000002", name: "Test Research Company", symbol: "TEST", exchange: "NASDAQ", instrument_id: id },
];
const page = { ...metadata, items, total: 2, limit: 20, offset: 0 };
async function settle() { await flush(() => setTimeout(240)); }

test("real directory search provides internal candidate and local company links, with actual selection navigation", async (t) => {
  const ui = await mount(t, CompanyDiscoverySearch, {}, async () => Response.json(page));
  await settle();
  const links = [...ui.document.querySelectorAll("a")];
  const apple = links.find((link) => link.textContent.includes("Apple Inc."));
  assert.equal(apple.getAttribute("href"), "/app/companies/discovery/0000320193?symbol=AAPL&exchange=NASDAQ");
  assert.equal(links.find((link) => link.textContent.includes("Test Research Company")).getAttribute("href"), `/app/companies/${id}`);
  await flush(() => apple.click());
  assert.deepEqual(ui.navigations, ["/app/companies/discovery/0000320193?symbol=AAPL&exchange=NASDAQ"]);
});

test("query changes hide old results immediately and reject late responses", async (t) => {
  const old = deferred();
  const newer = deferred();
  const ui = await mount(t, CompanyDiscoverySearch, {}, async (url) => {
    if (String(url).includes("query=MSFT")) return newer.promise;
    if (String(url).includes("query=AAPL")) return old.promise;
    return Response.json(page);
  });
  await settle();
  await ui.fill("input[type=search]", "AAPL");
  assert.doesNotMatch(ui.text(), /Apple Inc\./);
  await settle();
  await ui.fill("input[type=search]", "MSFT");
  await settle();
  await flush(() => newer.resolve(Response.json({ ...page, items: [{ ...items[0], name: "Microsoft Corp.", symbol: "MSFT" }] })));
  await flush(() => old.resolve(Response.json(page)));
  assert.match(ui.text(), /Microsoft Corp\./);
  assert.doesNotMatch(ui.text(), /Apple Inc\./);
});

test("a stale query 401 clears directory data and late success cannot restore it", async (t) => {
  const old = deferred();
  const current = deferred();
  let requests = 0;
  const ui = await mount(t, CompanyDiscoverySearch, {}, async () => ++requests === 1 ? old.promise : current.promise);
  await settle();
  await ui.fill("input[type=search]", "AAPL");
  await settle();
  await flush(() => old.resolve(Response.json({ detail: "authentication_required" }, { status: 401 })));
  assert.match(ui.text(), /Sign in to search/);
  await flush(() => current.resolve(Response.json(page)));
  assert.doesNotMatch(ui.text(), /Apple Inc\./);
  await ui.fill("input[type=search]", "MSFT");
  await settle();
  assert.equal(requests, 2);
});

test("returning to an earlier query hides its old response until a fresh request completes", async (t) => {
  const pendingB = deferred();
  const pendingA = deferred();
  let appleRequests = 0;
  const ui = await mount(t, CompanyDiscoverySearch, {}, async (url) => {
    if (String(url).includes("query=MSFT")) return pendingB.promise;
    if (String(url).includes("query=AAPL") && ++appleRequests > 1) return pendingA.promise;
    return Response.json(page);
  });
  await settle();
  await ui.fill("input[type=search]", "AAPL");
  await settle();
  assert.match(ui.text(), /Apple Inc\./);
  await ui.fill("input[type=search]", "MSFT");
  await settle();
  await ui.fill("input[type=search]", "AAPL");
  assert.doesNotMatch(ui.text(), /Apple Inc\./);
  const input = ui.document.querySelector("input[type=search]");
  await flush(() => input.dispatchEvent(new ui.document.defaultView.KeyboardEvent("keydown", { key: "Enter", bubbles: true })));
  assert.deepEqual(ui.navigations, []);
  await settle();
  await flush(() => pendingB.resolve(Response.json({ ...page, items: [{ ...items[0], name: "Microsoft Corp.", symbol: "MSFT" }] })));
  assert.doesNotMatch(ui.text(), /Microsoft Corp\./);
  await flush(() => pendingA.resolve(Response.json(page)));
  assert.match(ui.text(), /Apple Inc\./);
});

test("empty coverage and unavailable configuration have distinct messages and retries retain query", async (t) => {
  const urls = [];
  const ui = await mount(t, CompanyDiscoverySearch, {}, async (url) => {
    urls.push(String(url));
    return urls.length === 1 ? Response.json({ detail: "directory_not_configured" }, { status: 503 })
      : Response.json({ ...page, items: [], total: 0 });
  });
  await settle();
  assert.match(ui.text(), /source is not configured/);
  assert.doesNotMatch(ui.text(), /No match/);
  await ui.fill("input[type=search]", "uncovered");
  await settle();
  assert.match(ui.text(), /does not mean the company does not exist/);
  assert.match(urls.at(-1), /query=uncovered/);
});

test("locale and dialog changes preserve input; modifier clicks retain native link behavior", async (t) => {
  const ui = await mount(t, CompanyDiscoverySearch, {}, async () => Response.json(page));
  await settle();
  const link = [...ui.document.querySelectorAll("a")].find((node) => node.textContent.includes("Apple Inc."));
  const modified = new ui.document.defaultView.MouseEvent("click", { bubbles: true, cancelable: true, ctrlKey: true });
  await flush(() => link.dispatchEvent(modified));
  assert.equal(modified.defaultPrevented, false);
  assert.deepEqual(ui.navigations, []);
  await ui.fill("input[type=search]", "AAPL");
  await flush(() => ui.document.querySelector('button[aria-label="Close search"]').click());
  await ui.click("中文");
  await ui.click("打开搜索");
  assert.equal(ui.document.querySelector("input[type=search]").value, "AAPL");
  await settle();
  assert.match(ui.text(), /仅目录身份/);
  const input = ui.document.querySelector("input[type=search]");
  await flush(() => input.dispatchEvent(new ui.document.defaultView.KeyboardEvent("keydown", { key: "Enter", bubbles: true })));
  assert.deepEqual(ui.navigations, ["/app/companies/discovery/0000320193?symbol=AAPL&exchange=NASDAQ"]);
});

const { CompanyDirectoryDetail } = applicationModule("components/workspace/CompanyDirectoryDetail");
test("candidate details disclose source and missing data, without follow or research actions", async (t) => {
  const ui = await mount(t, CompanyDirectoryDetail, { cik: "0000320193", symbol: "AAPL", exchange: "NASDAQ" }, async () => Response.json({ ...metadata, company: items[0] }), "zh");
  await settle();
  assert.match(ui.text(), /Apple Inc\./);
  assert.match(ui.text(), /尚未收录，仅身份目录/);
  assert.match(ui.text(), /尚未接入本公司的报价/);
  assert.match(ui.text(), /抓取时间/);
  const actions = [...ui.document.querySelectorAll("button, a")].map((node) => node.textContent).join(" ");
  assert.doesNotMatch(actions, /发起研究|关注公司/);
});

test("empty-query Tab clears the main keyboard choice; ArrowUp selects the last result", async (t) => {
  const ui = await mount(t, CompanyDiscoverySearch, {}, async () => Response.json(page));
  await settle();
  const input = ui.document.querySelector("input[type=search]");
  const key = (value) => input.dispatchEvent(new ui.document.defaultView.KeyboardEvent("keydown", { key: value, bubbles: true, cancelable: true }));
  await flush(() => key("Tab"));
  await flush(() => key("Enter"));
  assert.deepEqual(ui.navigations, []);
  await flush(() => key("ArrowUp"));
  await flush(() => key("Enter"));
  assert.deepEqual(ui.navigations, [`/app/companies/${id}`]);
});

test("clearing a paged search resets the directory and rejects the previous page response", async (t) => {
  const previousPage = deferred();
  const clearedPage = deferred();
  const urls = [];
  let emptyRequests = 0;
  const ui = await mount(t, CompanyDiscoverySearch, {}, async (url) => {
    const params = new URL(String(url), "http://localhost").searchParams;
    urls.push({ query: params.get("query"), offset: params.get("offset") });
    if (!params.get("query")) return ++emptyRequests === 1 ? Response.json(page) : clearedPage.promise;
    if (params.get("offset") === "20") return previousPage.promise;
    return Response.json({ ...page, total: 40 });
  });
  await settle();
  assert.equal([...ui.document.querySelectorAll("button")].some((node) => node.textContent === "Clear Search"), false);
  await ui.fill("input[type=search]", "AAPL");
  await settle();
  await ui.click("Next");
  await settle();
  await ui.click("Clear Search");
  const input = ui.document.querySelector("input[type=search]");
  assert.equal(input.value, "");
  assert.equal(ui.document.activeElement, input);
  assert.doesNotMatch(ui.text(), /Apple Inc\./);
  await flush(() => input.dispatchEvent(new ui.document.defaultView.KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true })));
  assert.deepEqual(ui.navigations, []);
  await settle();
  assert.deepEqual(urls.at(-1), { query: "", offset: "0" });
  await flush(() => previousPage.resolve(Response.json({ ...page, items: [{ ...items[0], name: "Old page company" }], offset: 20, total: 40 })));
  assert.doesNotMatch(ui.text(), /Old page company/);
  await flush(() => clearedPage.resolve(Response.json(page)));
  assert.match(ui.text(), /Apple Inc\./);
  assert.ok(ui.document.querySelector('[role="dialog"]'));
});

test("localized clear stays usable on a failed search without reviving an expired session", async (t) => {
  const oldRequest = deferred();
  const ui = await mount(t, CompanyDiscoverySearch, {}, async (url) => {
    if (String(url).includes("query=AAPL")) return oldRequest.promise;
    return Response.json(page);
  }, "zh");
  await settle();
  await ui.fill("input[type=search]", "AAPL");
  await settle();
  await ui.click("清空搜索");
  await settle();
  assert.match(ui.text(), /Apple Inc\./);
  await flush(() => oldRequest.resolve(Response.json({ detail: "authentication_required" }, { status: 401 })));
  assert.match(ui.text(), /请登录后查询/);
  assert.doesNotMatch(ui.text(), /Apple Inc\./);
  await ui.fill("input[type=search]", "MSFT");
  await ui.click("清空搜索");
  await settle();
  assert.equal(ui.document.querySelector("input[type=search]").value, "");
  assert.equal(ui.document.activeElement, ui.document.querySelector("input[type=search]"));
  assert.match(ui.text(), /请登录后查询/);
  assert.deepEqual(ui.navigations, []);
});

test("closing and reopening preserves query, restores focus and contains Tab around enabled controls", async (t) => {
  const ui = await mount(t, CompanyDiscoverySearch, {}, async () => Response.json({ ...page, total: 40 }));
  await settle();
  await ui.fill("input[type=search]", "AAPL");
  await settle();
  const close = ui.document.querySelector('button[aria-label="Close search"]');
  const next = [...ui.document.querySelectorAll("button")].find((node) => node.textContent === "Next");
  close.focus();
  const backward = new ui.document.defaultView.KeyboardEvent("keydown", { key: "Tab", shiftKey: true, bubbles: true, cancelable: true });
  await flush(() => close.dispatchEvent(backward));
  assert.equal(backward.defaultPrevented, true);
  assert.equal(ui.document.activeElement, next);
  const forward = new ui.document.defaultView.KeyboardEvent("keydown", { key: "Tab", bubbles: true, cancelable: true });
  await flush(() => next.dispatchEvent(forward));
  assert.equal(ui.document.activeElement, close);
  assert.equal(ui.document.body.style.overflow, "hidden");
  await flush(() => close.dispatchEvent(new ui.document.defaultView.KeyboardEvent("keydown", { key: "Escape", bubbles: true, cancelable: true })));
  assert.equal(ui.document.querySelector('[role="dialog"]'), null);
  assert.equal(ui.document.body.style.overflow, "");
  assert.equal(ui.document.activeElement.textContent, "Open search");
  await ui.click("Open search");
  const input = ui.document.querySelector("input[type=search]");
  assert.equal(input.value, "AAPL");
  assert.equal(ui.document.activeElement, input);
  assert.equal(ui.document.body.style.overflow, "hidden");
  await settle();
});
