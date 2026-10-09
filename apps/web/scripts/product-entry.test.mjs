import assert from "node:assert/strict";
import test from "node:test";

const previewUrl = process.env.PRODUCT_PREVIEW_URL;

test("full reference home preserves every source section and interaction asset with own branding in both locales", {
  skip: previewUrl ? false : "Set PRODUCT_PREVIEW_URL to a running local product server",
}, async () => {
  for (const [locale, lang, heading] of [
    [undefined, "zh-CN", "欢迎来到你的"],
    ["unsupported", "zh-CN", "欢迎来到你的"],
    ["zh", "zh-CN", "欢迎来到你的"],
    ["en", "en", "Welcome to your"],
  ]) {
    const headers = locale ? { Cookie: `tradeagent-preview-locale=${locale}` } : {};
    const response = await fetch(previewUrl, {
      headers,
    });
    assert.equal(response.status, 200);
    const html = await response.text();
    assert.match(html, new RegExp(`<html[^>]*lang="${lang}"`));
    assert.match(html, /<title>TradeAgent/);
    assert.ok(html.match(/<h1[\s\S]*?<\/h1>/)?.[0].includes(heading));
    assert.ok(html.includes("Full reference preview"));
    assert.ok(html.includes("Original media, reviews, features and links are reference material"));
    assert.match(html, /<meta name="robots" content="noindex, nofollow"/);
    for (const placement of ["header", "footer"]) {
      assert.match(html, new RegExp(`<img[^>]*src="/tradeagent-${placement}\\.svg"[^>]*alt="TradeAgent"`));
    }

    const reference = await fetch(new URL("/references/simply-wall-st", previewUrl), { headers });
    assert.equal(reference.status, 200);
    const referenceHtml = await reference.text();
    const main = html.match(/<main class="home-content">([\s\S]*?)<\/main>/)?.[1];
    const referenceMain = referenceHtml.match(/<main class="home-content">([\s\S]*?)<\/main>/)?.[1];
    assert.ok(main, "Missing complete homepage body");
    assert.equal(main.match(/<section\b/g)?.length, 11, "A source section was removed");
    assert.equal(main, referenceMain, "Homepage content, media or controls differ from the full reference");
    assert.ok(referenceHtml.includes("/media/ad4997bab3155971.svg"));
    assert.ok(referenceHtml.includes("/media/1807de39bdbfee0d.svg"));
    assert.ok(!referenceHtml.includes("/tradeagent-header.svg"));
    const destinations = [...html.matchAll(/<a\b[^>]*\bhref="([^"]+)"/g)].map((match) => match[1]);
    assert.ok(destinations.includes("/app"));
    assert.ok(destinations.includes("/login"));
    assert.ok(destinations.includes("/register"));
    assert.ok(destinations.length > 10);
    assert.ok(destinations.some((href) => href.startsWith("https://simplywall.st/")), "Source reference links should be preserved and disclosed");
  }
});
