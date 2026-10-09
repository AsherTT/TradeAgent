import assert from "node:assert/strict";
import test from "node:test";
import { applicationModule, mount } from "./component-harness.mjs";
import { JSDOM } from "jsdom";

test("company preview switches all static content and preserves source links and dates", async (t) => {
  const { CompanySourcePreview } = applicationModule("app/labs/r1-company-data-status/CompanySourcePreview");
  const page = await mount(t, CompanySourcePreview, {}, () => { throw new Error("Static preview must not request account data"); }, "zh");
  assert.ok(page.text().includes("公司分析与财务数据更新状态"));
  assert.ok(page.text().includes("数据来源"));
  assert.ok(page.text().includes("分析模型与雪花图"));
  assert.ok(page.text().includes("行业与板块指标"));
  assert.ok(page.text().includes("分析师来源"));
  assert.ok(page.text().includes("其余 85 位分析师"));
  assert.equal(page.document.querySelector('[aria-label="分析师来源"] tbody').rows.length, 3);
  assert.ok(page.text().includes("Accountability Research Corporation"));
  assert.ok(page.text().includes("现金流量表"));
  assert.ok(!page.text().includes("Earnings"), "Chinese table must translate the earnings labels");
  const links = [...page.document.querySelectorAll("a")].map((a) => a.getAttribute("href"));
  const tables = page.document.querySelectorAll("table").length;
  await page.click("EN");
  assert.ok(page.text().includes("Company Analysis and Financial Data Status"));
  assert.ok(page.text().includes("Data Sources"));
  assert.ok(page.text().includes("Analysis Model and Snowflake"));
  assert.ok(page.text().includes("Analyst Sources"));
  assert.ok(page.text().includes("the remaining 85 analysts"));
  assert.equal(page.document.querySelector('[aria-label="Analyst Sources"] tbody').rows.length, 3);
  assert.ok(page.text().includes("Accountability Research Corporation"));
  assert.ok(page.text().includes("Cash flow statement"));
  assert.ok(page.text().includes("2026/10/07 18:18"));
  assert.equal(page.document.documentElement.lang, "en");
  assert.match(page.document.cookie, /tradeagent-preview-locale=en/);
  assert.equal(page.document.querySelector('[aria-label="English"]').getAttribute("aria-pressed"), "true");
  assert.deepEqual([...page.document.querySelectorAll("a")].map((a) => a.getAttribute("href")), links);
  assert.equal(page.document.querySelectorAll("table").length, tables);
  await page.click("中文");
  assert.ok(page.text().includes("公司分析与财务数据更新状态"));
  assert.ok(page.text().includes("静态样本"));
  assert.equal(page.document.documentElement.lang, "zh-CN");
  assert.match(page.document.cookie, /tradeagent-preview-locale=zh/);
});

test("account language switch preserves unfinished registration input", async (t) => {
  const { AuthForm } = applicationModule("components/accounts/AuthForm");
  const page = await mount(t, AuthForm, { mode: "register" }, () => { throw new Error("Switching language must not submit a registration"); }, "zh");
  await page.fill('input[type="email"]', "language-check@example.test");
  await page.fill('input[type="password"]', "local-language-test-password");
  await page.click("EN");
  assert.ok(page.text().includes("Create a TradeAgent account with your email."));
  assert.equal(page.document.querySelector('input[type="email"]').value, "language-check@example.test");
  assert.equal(page.document.querySelector('input[type="password"]').value, "local-language-test-password");
  await page.click("中文");
  assert.ok(page.text().includes("使用邮箱创建 TradeAgent 账户。"));
  assert.equal(page.document.querySelector('input[type="email"]').value, "language-check@example.test");
});

if (process.env.BILINGUAL_PREVIEW_URL) {
  test("public pages honor the shared locale cookie in their initial HTML and language controls", async () => {
    const routes = [
      ["/login", "欢迎回来", "Welcome back", "TradeAgent — 登录", "TradeAgent — Sign in"],
      ["/register", "建立你的研究工作台", "Build your research workspace", "TradeAgent — 创建账户", "TradeAgent — Create account"],
      ["/labs/r1-company-data-status", "公司来源组件验证", "Company source component preview", "公司来源组件验证 | TradeAgent", "Company source component preview | TradeAgent"],
      ["/labs/function-integration", "功能联调稿，尚未获得设计认可。", "Functional integration preview, design unapproved.", "功能联调预览 | TradeAgent", "Functional integration preview | TradeAgent"],
    ];
    for (const [path, zh, en, zhTitle, enTitle] of routes) {
      for (const locale of ["zh", "en"]) {
        const response = await fetch(new URL(path, process.env.BILINGUAL_PREVIEW_URL), { headers: { Cookie: `tradeagent-preview-locale=${locale}` } });
        assert.equal(response.status, 200);
        const dom = new JSDOM(await response.text());
        const document = dom.window.document;
        assert.equal(document.documentElement.lang, locale === "zh" ? "zh-CN" : "en");
        assert.equal(document.title, locale === "zh" ? zhTitle : enTitle);
        assert.ok(document.querySelector("main, aside").textContent.includes(locale === "zh" ? zh : en));
        assert.equal(document.querySelector(`[aria-label="${locale === "zh" ? "中文" : "English"}"]`).getAttribute("aria-pressed"), "true");
        dom.window.close();
      }
    }
  });
}
