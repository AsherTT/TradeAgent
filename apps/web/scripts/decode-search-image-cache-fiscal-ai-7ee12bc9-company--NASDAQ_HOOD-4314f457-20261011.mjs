import { createHash } from "node:crypto";
import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pageKey = "fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457";
const research = path.join(root, "docs/research", pageKey);
const output = path.join(root, "public/sites", pageKey, "search-images-20261011");
const inventory = JSON.parse(await readFile(path.join(research, "search-live-images-20261011.json"), "utf8"));
const observedByUrl = new Map(inventory.map((asset) => [asset.src, asset]));
const hood = inventory.find((asset) => new URL(asset.src).searchParams.get("ticker") === "HOOD");
const files = (await readdir(research)).filter((name) => name === "cached-hood-logo-20261011.json" || /^cached-search-logos-batch-\d{3}-20261011\.json$/.test(name) || /^cached-search-logo-[A-Za-z0-9_.-]+-20261011\.json$/.test(name)).sort();
const byUrl = new Map();
const byTarget = new Map();
const failures = [];

await mkdir(output, { recursive: true });
for (const sourceFile of files) {
  const parsed = JSON.parse((await readFile(path.join(research, sourceFile), "utf8")).replace(/^\uFEFF/, ""));
  const records = Array.isArray(parsed) ? parsed : [parsed];
  for (const record of records) {
    const url = record.url ?? (sourceFile === "cached-hood-logo-20261011.json" ? hood?.src : undefined);
    if (!url || !observedByUrl.has(url)) throw new Error(`Unobserved image URL in ${sourceFile}`);
    const observed = new URL(url);
    if (observed.pathname !== "/api/company-logo/") throw new Error(`Unexpected cached endpoint in ${sourceFile}`);
    const ticker = observed.searchParams.get("ticker");
    if (!ticker || !/^[A-Za-z0-9_.-]+$/.test(ticker)) throw new Error(`Invalid observed ticker in ${sourceFile}`);
    if (record.base64Encoded !== true || typeof record.content !== "string" || !/^[A-Za-z0-9+/]*={0,2}$/.test(record.content)) {
      failures.push({ observedUrl: url, sourceFile, status: "failed", reason: "Missing or malformed base64 cache payload" });
      continue;
    }
    const bytes = Buffer.from(record.content, "base64");
    if (bytes.toString("base64") !== record.content) throw new Error(`Noncanonical base64 payload in ${sourceFile}`);
    const png = bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
    const jpeg = bytes.length > 3 && bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
    const mimeType = png ? "image/png" : jpeg ? "image/jpeg" : null;
    if (!mimeType || (record.mimeType && record.mimeType !== mimeType)) {
      failures.push({ observedUrl: url, sourceFile, status: "failed", reason: "PNG/JPEG signature missing or MIME mismatch" });
      continue;
    }
    const extension = png ? ".png" : ".jpg";
    const target = path.join(output, `logo-${ticker}${extension}`);
    const sha256 = createHash("sha256").update(bytes).digest("hex");
    if (byTarget.has(target) && byTarget.get(target) !== sha256) throw new Error(`Conflicting cached bytes for ${ticker}`);
    byTarget.set(target, sha256);
    await writeFile(target, bytes);
    byUrl.set(url, {
      observedUrl: url,
      alt: observedByUrl.get(url).alt,
      ticker,
      status: "downloaded-from-loaded-resource-cache",
      method: "Parent browser Page.getResourceContent of an already-loaded observed image; local base64 decode only",
      sourceFile,
      sourceFrameURL: record.sourceFrameURL ?? record.sourceframeURL ?? null,
      mimeType,
      signatureVerified: true,
      path: path.relative(root, target).split(path.sep).join("/"),
      bytes: bytes.length,
      sha256,
    });
  }
}

const assets = [...byUrl.values()];
await writeFile(path.join(research, "search-image-cache-manifest-20261011.json"), `${JSON.stringify({
  generatedAt: new Date().toISOString(),
  inventory: "search-live-images-20261011.json",
  observationURL: "https://fiscal.ai/company/NASDAQ_HOOD/",
  httpEvidence: "search-image-http-probes-20261011.json",
  httpDownloadManifest: "search-image-download-manifest-20261011.json",
  policy: "HTTP failure evidence is preserved; cached bytes are decoded without new network requests, browser control, image conversion or logo reconstruction",
  sourceFiles: files,
  assets,
  failures,
  missingLogoUrls: inventory.filter((asset) => new URL(asset.src).pathname === "/api/company-logo/" && !byUrl.has(asset.src)).map((asset) => asset.src),
}, null, 2)}\n`);
console.log(JSON.stringify({ decoded: assets.length, failed: failures.length, pathMap: Object.fromEntries(assets.map((asset) => [asset.ticker, `/${asset.path.replace(/^public\//, "")}`])) }));
