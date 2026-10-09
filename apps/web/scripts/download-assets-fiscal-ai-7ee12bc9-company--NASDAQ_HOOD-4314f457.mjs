import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { gunzipSync } from 'node:zlib';

const root = process.cwd();
const research = path.join(root, 'docs/research/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457');
const output = path.join(root, 'public/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457');
const fontOutput = path.join(root, 'public/sites/fiscal-ai-7ee12bc9/shared/fonts');
const inventory = JSON.parse(gunzipSync(await readFile(path.join(research, 'asset-inventory.json.gz'))).toString('utf8'));
const allowedHosts = new Set(['fiscal.ai', 'code.highcharts.com', 'a.storyblok.com', 'fonts.googleapis.com', 'fonts.gstatic.com']);
const results = [];
const manifestPath = path.join(research, 'download-manifest.json');
let previousResults = [];
try {
  previousResults = JSON.parse(await readFile(manifestPath, 'utf8'));
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
const previousByUrl = new Map(previousResults.map(asset => [asset.url, asset]));

async function download(asset) {
  const url = new URL(asset.url);
  if (!allowedHosts.has(url.hostname)) throw new Error('Unexpected asset host');
  const digest = createHash('sha256').update(asset.url).digest('hex').slice(0, 12);
  const extension = asset.kind === 'stylesheet' ? '.css' : path.extname(url.pathname) || '.png';
  const target = path.join(asset.kind === 'font' ? fontOutput : output, `${digest}${extension}`);
  const previous = previousByUrl.get(asset.url);
  if (previous && !previous.error) {
    try {
      const bytes = await readFile(target);
      if (bytes.length === previous.bytes && createHash('sha256').update(bytes).digest('hex') === previous.sha256) {
        results.push(previous);
        return asset.kind === 'stylesheet' ? bytes.toString('utf8') : '';
      }
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  try {
    const response = await fetch(asset.url, {
      signal: AbortSignal.timeout(12000),
      headers: { 'User-Agent': 'Mozilla/5.0 Chrome/130.0.0.0 Safari/537.36' },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (!allowedHosts.has(new URL(response.url).hostname)) throw new Error('Unexpected redirect');
    const bytes = Buffer.from(await response.arrayBuffer());
    await writeFile(target, bytes);
    results.push({ url: asset.url, kind: asset.kind, path: path.relative(root, target).split(path.sep).join('/'), bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') });
    return asset.kind === 'stylesheet' ? bytes.toString('utf8') : '';
  } catch (error) {
    results.push({ url: asset.url, kind: asset.kind, error: error.message });
    return '';
  }
}

await mkdir(output, { recursive: true });
await mkdir(fontOutput, { recursive: true });
const fontUrls = new Set();
for (let index = 0; index < inventory.assets.length; index += 4) {
  const css = await Promise.all(inventory.assets.slice(index, index + 4).map(download));
  for (const text of css) {
    for (const match of text.matchAll(/url\((https:\/\/fonts\.gstatic\.com\/[^)]+)\)/g)) {
      fontUrls.add(match[1]);
    }
  }
}
const fonts = [...fontUrls].map(url => ({ url, kind: 'font' }));
for (let index = 0; index < fonts.length; index += 4) {
  await Promise.all(fonts.slice(index, index + 4).map(download));
}
results.sort((left, right) => left.url.localeCompare(right.url));
await writeFile(manifestPath, `${JSON.stringify(results, null, 2)}\n`);
console.log(JSON.stringify({ downloaded: results.filter(item => !item.error).length, failed: results.filter(item => item.error).length, fonts: results.filter(item => item.kind === 'font' && !item.error).length }));
