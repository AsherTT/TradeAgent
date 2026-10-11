import { readFile, writeFile, mkdir } from "node:fs/promises";
import { createHash } from "node:crypto";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const page = "fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457";
const artifacts = resolve(root, "docs/research", page);
const destination = resolve(root, "public/sites", page, "listing-flags-20261012");
const rows = JSON.parse(await readFile(resolve(artifacts, "listings-expanded-data-20261012.json"), "utf8"));
const urls = [...new Set(rows.flatMap(row => row.children.map(child => {
  const image = new URL(child.flag, "https://fiscal.ai");
  const source = new URL(image.searchParams.get("url") ?? image.href);
  if (source.origin !== "https://cdn.fiscal.ai" || !/^\/flags\/[A-Z]+\.svg$/.test(source.pathname)) {
    throw new Error("Unexpected captured flag URL");
  }
  return source.href;
})))];
await mkdir(destination, { recursive: true });
const manifest = [];
for (let offset = 0; offset < urls.length; offset += 4) {
  const batch = await Promise.all(urls.slice(offset, offset + 4).map(async url => {
    const filename = new URL(url).pathname.split("/").at(-1);
    const path = resolve(destination, filename);
    let bytes;
    let cached = false;
    try { bytes = await readFile(path); cached = true; } catch {
      const response = await fetch(url, { signal: AbortSignal.timeout(15000) });
      if (!response.ok) throw new Error(`Flag request failed: ${filename} ${response.status}`);
      bytes = Buffer.from(await response.arrayBuffer());
    }
    if (!bytes.toString("utf8").includes("<svg")) throw new Error(`Invalid SVG: ${filename}`);
    if (!cached) await writeFile(path, bytes);
    return { source: url, file: `public/sites/${page}/listing-flags-20261012/${filename}`, bytes: bytes.length,
      sha256: createHash("sha256").update(bytes).digest("hex") };
  }));
  manifest.push(...batch);
}
await writeFile(resolve(artifacts, "listing-flags-manifest-20261012.json"), `${JSON.stringify(manifest, null, 2)}\n`);
const expected = {
  "/company/NASDAQ_NVDA/": 40, "/company/NASDAQ_AAPL/": 36, "/company/NASDAQ_GOOG/": 65,
  "/company/NASDAQ_MSFT/": 42, "/company/NASDAQ_AMZN/": 39, "/company/NASDAQ_SPCX/": 27,
  "/company/NYSE_TSM/": 15, "/company/NASDAQ_META/": 38, "/company/NASDAQ_AVGO/": 29,
};
const listings = {};
for (const [href, count] of Object.entries(expected)) {
  const row = rows.find(item => item.href === href);
  if (!row || row.children.length !== count) throw new Error(`Missing captured listings: ${href}`);
  listings[href] = row.children.map(child => {
    const image = new URL(child.flag, "https://fiscal.ai");
    const source = new URL(image.searchParams.get("url") ?? image.href);
    const filename = source.pathname.split("/").at(-1);
    return { href: child.href, market: child.market, flag: `/sites/${page}/listing-flags-20261012/${filename}`, flagAlt: child.alt };
  });
}
await writeFile(resolve(root, "src/components/sites", page, "search-listing-data.ts"),
  `import type { SearchListing } from "./search-types";\n\n/** Captured source listings, including URL aliases; not a live securities directory. */\nexport const referenceListings: Readonly<Record<string, readonly SearchListing[]>> = ${JSON.stringify(listings, null, 2)};\n`);
console.log(JSON.stringify({ companies: Object.keys(listings).length, listings: Object.values(listings).reduce((count, items) => count + items.length, 0), flags: manifest.length, signatureValidated: true }));
