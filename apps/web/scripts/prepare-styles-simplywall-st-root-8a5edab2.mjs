import { readFile, writeFile } from "node:fs/promises";
import postcss from "postcss";

const research = "docs/research/simplywall-st-1b042a47/root-8a5edab2";
const media = JSON.parse(await readFile(`${research}/downloaded-media-20261006.json`, "utf8"));
const mediaByFilename = new Map(media.assets.map((asset) => [new URL(asset.url).pathname.split("/").pop(), asset.localPath]));
const sheets = ["3d8ac1cfee66430f.css", "5f8932b378b8f11b.css", "72584aff0dd8d4f5.css", "75da1eeb5f512dde.css"];

function splitSelectors(selector) {
  const parts = [];
  let start = 0;
  let depth = 0;
  let quote = "";
  for (let i = 0; i < selector.length; i++) {
    const character = selector[i];
    if (character === "\\") { i++; continue; }
    if (quote) { if (character === quote) quote = ""; continue; }
    if (character === '"' || character === "'") { quote = character; continue; }
    if (character === "(" || character === "[") depth++;
    if (character === ")" || character === "]") depth--;
    if (character === "," && depth === 0) { parts.push(selector.slice(start, i)); start = i + 1; }
  }
  parts.push(selector.slice(start));
  return parts;
}

const prepared = [];
for (const name of sheets) {
  const sheet = postcss.parse(await readFile(`${research}/source-css/${name}`, "utf8"));
  sheet.walkAtRules("font-face", (rule) => {
    if (!rule.toString().includes("webflow-icons")) rule.remove();
  });
  sheet.walkRules((rule) => {
    if (rule.parent.type === "atrule" && /keyframes$/.test(rule.parent.name)) return;
    rule.selector = splitSelectors(rule.selector).map((selector) => {
      const scoped = selector.trim().replace(/(^|[\s>+~])(?:html|body)(?=[\s.#:\[>+~]|$)/g, "$1.sws-source").replace(/:root/g, ".sws-source").replace(/^\.home-page(?=[\s.#:\[>+~]|$)/, ".sws-source.home-page");
      return scoped.startsWith(".sws-source") ? scoped : `:where(.sws-source) ${scoped}`;
    }).join(",");
  });
  sheet.walkDecls((declaration) => {
    if (declaration.prop === "font-family" || declaration.prop.startsWith("--")) {
      declaration.value = declaration.value
        .replace(/["']?(?:Stkbureausans|BureauSans)["']?/gi, "var(--font-sws-bureau-sans)")
        .replace(/["']?(?:Stkbureauserif|BureauSerif)["']?/gi, "var(--font-sws-bureau-serif)")
        .replace(/["']?Inter["']?/g, "var(--font-sws-inter)");
    }
    declaration.value = declaration.value.replace(/url\((["']?)([^)]*)\1\)/g, (match, quote, url) => {
      if (url.startsWith("data:")) return match;
      const local = mediaByFilename.get(url.split("/").pop());
      if (!local) throw new Error(`Unmapped stylesheet asset in ${name}: ${url}`);
      return `url("${local}")`;
    });
  });
  prepared.push(`/* Captured source: ${research}/source-css/${name}. Scoped reference CSS; no scripts. */\n${sheet.toString()}`);
}
await writeFile("src/components/sites/simplywall-st-1b042a47/shared/source-styles.css", prepared.join("\n") + "\n");
console.log("Prepared four captured stylesheets with local fonts and scoped selectors.");
