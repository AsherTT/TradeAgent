import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { test } from "node:test";
import { runInNewContext } from "node:vm";
import ts from "typescript";

const messagesUrl = new URL("../src/components/sites/simplywall-st-1b042a47/shared/i18n/messages.ts", import.meta.url);
const chinese = JSON.parse(readFileSync(new URL("./zh.json", messagesUrl), "utf8"));
const sourceTexts = JSON.parse(readFileSync(new URL("../docs/research/simplywall-st-1b042a47/root-8a5edab2/locale-source-text.json", import.meta.url), "utf8"));
const compiled = ts.transpileModule(readFileSync(messagesUrl, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, esModuleInterop: true },
}).outputText;
const compiledModule = { exports: {} };
runInNewContext(compiled, {
  exports: compiledModule.exports,
  module: compiledModule,
  require: createRequire(messagesUrl),
});
const { resolveLocale, languageTag, translate } = compiledModule.exports;

test("first visits and unsupported preferences use Chinese; valid choices survive", () => {
  for (const value of [undefined, "", "de", "ZH", "constructor", "en-US"]) {
    assert.equal(resolveLocale(value), "zh");
  }
  assert.equal(resolveLocale("zh"), "zh");
  assert.equal(resolveLocale("en"), "en");
  assert.equal(languageTag("zh"), "zh-CN");
  assert.equal(languageTag("en"), "en");
});

test("every inspected homepage text and accessible image label has a nonempty translation", () => {
  assert.ok(sourceTexts.length > 250, "the inventory must cover the complete homepage");
  for (const english of sourceTexts) {
    assert.ok(Object.hasOwn(chinese, english), `Missing translation: ${english}`);
    assert.ok(chinese[english].trim(), `Empty translation: ${english}`);
    assert.equal(translate("zh", english), chinese[english]);
  }
});

test("English retains every source string exactly, including punctuation and spacing", () => {
  for (const english of sourceTexts) assert.equal(translate("en", english), english);
});

test("unknown content safely falls back to its own text, including object prototype names", () => {
  for (const english of ["Future untranslated text", "constructor", "toString", "__proto__", ""]) {
    assert.equal(translate("zh", english), english);
  }
});

// Optional reference check: LOCALIZATION_PREVIEW_URL=http://127.0.0.1:3107/references/simply-wall-st
if (process.env.LOCALIZATION_PREVIEW_URL) {
  test("initial server HTML uses the stored locale without a wrong-language first render", async () => {
    for (const [cookie, lang, heading] of [
      [undefined, "zh-CN", "欢迎来到你的"],
      ["zh", "zh-CN", "欢迎来到你的"],
      ["en", "en", "Welcome to your"],
      ["unsupported", "zh-CN", "欢迎来到你的"],
    ]) {
      const response = await fetch(process.env.LOCALIZATION_PREVIEW_URL, {
        headers: cookie ? { Cookie: `tradeagent-preview-locale=${cookie}` } : {},
      });
      assert.equal(response.status, 200);
      const html = await response.text();
      assert.match(html, new RegExp(`<html[^>]*lang="${lang}"`));
      assert.ok(html.match(/<h1[\s\S]*?<\/h1>/)?.[0].includes(heading), `Incorrect heading for ${cookie}`);
      assert.ok(html.includes(`<title>${translate(resolveLocale(cookie), "Simply Wall St — Local reference preview")}</title>`));
    }
  });
}
