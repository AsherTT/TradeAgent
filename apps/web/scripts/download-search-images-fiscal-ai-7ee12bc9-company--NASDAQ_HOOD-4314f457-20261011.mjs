import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pageKey = "fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457";
const research = path.join(root, "docs/research", pageKey);
const output = path.join(root, "public/sites", pageKey, "search-images-20261011");
const inventoryFile = "search-live-images-20261011.json";
const probeFile = "search-image-http-probes-20261011.json";
const manifestFile = "search-image-download-manifest-20261011.json";
const inventory = JSON.parse(await readFile(path.join(research, inventoryFile), "utf8"));
const probes = JSON.parse(await readFile(path.join(research, probeFile), "utf8"));
const blockedHosts = new Set(probes.filter((probe) => probe.httpStatus === 429).map((probe) => new URL(probe.requestedUrl).hostname));
const results = [];
const imageExtensions = {
  "image/svg+xml": ".svg",
  "image/png": ".png",
  "image/jpeg": ".jpg",
  "image/webp": ".webp",
  "image/gif": ".gif",
  "image/avif": ".avif",
  "image/x-icon": ".ico",
  "image/vnd.microsoft.icon": ".ico",
};

await mkdir(output, { recursive: true });
for (const asset of inventory) {
  const observed = new URL(asset.src);
  if (observed.protocol !== "https:" || observed.hostname !== "fiscal.ai") {
    throw new Error("Inventory must contain observed public Fiscal image URLs only");
  }

  let requestedUrl = asset.src;
  let derivation = "Observed image src, unchanged";
  if (observed.pathname === "/_next/image/") {
    const original = new URL(observed.searchParams.get("url"));
    if (original.protocol !== "https:" || original.hostname !== "cdn.fiscal.ai" || !/^\/flags\/[A-Z]{2}\.svg$/.test(original.pathname)) {
      throw new Error("Unexpected flag original URL in observed optimizer src");
    }
    requestedUrl = original.href;
    derivation = "Decoded url parameter of the observed Next image src; original flag asset";
  } else if (observed.pathname !== "/api/company-logo/") {
    throw new Error("Unexpected observed image endpoint");
  }

  const entry = { alt: asset.alt, observedUrl: asset.src, requestedUrl, derivation };
  const host = new URL(requestedUrl).hostname;
  if (blockedHosts.has(host)) {
    const probe = probes.find((item) => item.requestedUrl === requestedUrl);
    results.push({
      ...entry,
      status: probe ? "failed-probe" : "not-attempted",
      ...(probe ? { httpStatus: probe.httpStatus } : {}),
      reason: "HTTP 429 observed on fiscal.ai; host circuit breaker prevents bulk retries",
      evidence: probeFile,
    });
    continue;
  }

  try {
    const response = await fetch(requestedUrl, {
      redirect: "manual",
      signal: AbortSignal.timeout(15000),
    });
    const contentType = response.headers.get("content-type")?.split(";")[0].trim() ?? "";
    if (!response.ok) {
      if (response.status === 429) blockedHosts.add(host);
      results.push({ ...entry, status: "failed", httpStatus: response.status, contentType });
      continue;
    }
    const bytes = Buffer.from(await response.arrayBuffer());
    const extension = imageExtensions[contentType];
    const isFlag = new URL(requestedUrl).hostname === "cdn.fiscal.ai";
    if (!extension || bytes.length === 0 || (isFlag && (contentType !== "image/svg+xml" || !bytes.toString("utf8").includes("<svg")))) {
      results.push({ ...entry, status: "failed", httpStatus: response.status, reason: "Response is not the expected image asset" });
      continue;
    }
    const digest = createHash("sha256").update(bytes).digest("hex");
    const assetName = isFlag
      ? `flag-${path.basename(new URL(requestedUrl).pathname, ".svg")}`
      : `logo-${observed.searchParams.get("companyKey") ?? `${observed.searchParams.get("exchange")}-${observed.searchParams.get("ticker")}`}`;
    const safeName = assetName.replace(/[^A-Za-z0-9_-]/g, "-");
    const target = path.join(output, `${safeName}-${digest.slice(0, 12)}${extension}`);
    await writeFile(target, bytes);
    results.push({
      ...entry,
      status: "downloaded",
      httpStatus: response.status,
      contentType,
      path: path.relative(root, target).split(path.sep).join("/"),
      bytes: bytes.length,
      sha256: digest,
    });
  } catch {
    // Do not print network/proxy error messages, which can contain credentials.
    results.push({ ...entry, status: "failed", reason: "Network error or timeout; no asset written" });
  }
}

await writeFile(path.join(research, manifestFile), `${JSON.stringify({
  inventory: inventoryFile,
  probeEvidence: probeFile,
  generatedAt: new Date().toISOString(),
  policy: "Only observed public image URLs or their explicit original flag url parameter; no logo reconstruction; no retries after HTTP 429",
  assets: results,
}, null, 2)}\n`);
console.log(JSON.stringify({
  inventory: results.length,
  downloaded: results.filter((item) => item.status === "downloaded").length,
  failed: results.filter((item) => item.status.startsWith("failed")).length,
  notAttempted: results.filter((item) => item.status === "not-attempted").length,
}));
