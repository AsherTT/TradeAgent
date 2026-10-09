import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";

// Download only public media URLs already observed in the source-page inventory.
const root = process.cwd();
const research = "docs/research/simplywall-st-1b042a47/root-8a5edab2";
const destination = "public/sites/simplywall-st-1b042a47/root-8a5edab2/media";
const inventory = JSON.parse(await readFile(path.join(root, research, "page-assets-20261006-current.json"), "utf8"));
const allowedHosts = new Set(["marketing.simplywall.st", "simplywall.st"]);
const captured = JSON.parse(await readFile(path.join(root, research, "computed-full-20261006-1440.json"), "utf8"));
const observed = new Map(inventory.assets.filter((asset) => asset.kind === "image").map((asset) => [asset.url, asset]));
for (const section of captured) {
  for (const node of section.nodes) {
    if (node.tag !== "img" || !node.attributes.src) continue;
    const url = node.attributes.src;
    if (!observed.has(url)) observed.set(url, { kind: "image", url, id: createHash("sha256").update(url).digest("hex").slice(0, 16) });
  }
}
const assets = [...observed.values()].filter((asset) => {
  if (asset.kind !== "image") return false;
  const url = new URL(asset.url);
  return url.protocol === "https:" && allowedHosts.has(url.hostname);
});
const extensions = new Map([
  ["image/svg+xml", "svg"], ["image/png", "png"], ["image/jpeg", "jpg"],
  ["image/webp", "webp"], ["image/avif", "avif"], ["image/gif", "gif"],
]);
const results = [];
const previous = JSON.parse(await readFile(path.join(root, research, "downloaded-media-20261006.json"), "utf8"));
const cached = new Map(previous.assets.filter((asset) => !asset.error).map((asset) => [asset.url, asset]));
await mkdir(path.join(root, destination), { recursive: true });
let next = 0;
async function worker() {
  while (next < assets.length) {
    const asset = assets[next++];
    try {
      const existing = cached.get(asset.url);
      if (existing) {
        const saved = await readFile(path.join(root, "public", existing.localPath));
        if (createHash("sha256").update(saved).digest("hex") === existing.sha256) {
          results.push(existing);
          continue;
        }
      }
      const response = await fetch(asset.url, { signal: AbortSignal.timeout(25000) });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const contentType = response.headers.get("content-type")?.split(";")[0];
      const extension = extensions.get(contentType);
      if (!extension) throw new Error(`Unexpected content type: ${contentType}`);
      const bytes = Buffer.from(await response.arrayBuffer());
      const filename = `${asset.id}.${extension}`;
      await writeFile(path.join(root, destination, filename), bytes);
      results.push({ url: asset.url, localPath: `/${destination.slice(7)}/${filename}`, bytes: bytes.length, contentType, sha256: createHash("sha256").update(bytes).digest("hex") });
    } catch (error) {
      results.push({ url: asset.url, error: String(error) });
    }
  }
}
await Promise.all(Array.from({ length: 4 }, worker));
results.sort((a, b) => a.url.localeCompare(b.url));
await writeFile(path.join(root, research, "downloaded-media-20261006.json"), JSON.stringify({ sourceInventory: ["page-assets-20261006-current.json", "computed-full-20261006-1440.json"], method: "public asset HTTP download after normal source access succeeded", excluded: "Third-party analytics/tracking image requests are not website media and are excluded.", assets: results }, null, 2) + "\n");
const failures = results.filter((result) => result.error);
console.log(JSON.stringify({ downloaded: results.length - failures.length, failures }, null, 2));
if (failures.length) process.exitCode = 1;
