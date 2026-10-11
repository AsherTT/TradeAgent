# Fiscal 搜索可见图片下载（2026-10-11）

## 来源及范围

- 来源清单：`search-live-images-20261011.json`，实际共 25 个去重 URL：21 个公司/基金 logo、US/SA/AU/BR 四面国旗。
- 仅请求已经观察到的公开图片 URL。国旗原图 URL 来自已观察的 Next 图片 URL 的 `url` 参数，不猜测其他素材路径。
- 此次没有修改组件、全局样式或浏览器状态，也没有生成或重画 logo。

## HTTP 探测和结果

- HOOD logo 原 URL：429，响应是 HTML，不保存为图片。
- US 国旗 Next 优化 URL：429，响应是 HTML，不保存为图片。
- US 国旗原图 `https://cdn.fiscal.ai/flags/US.svg`：200、`image/svg+xml`、1420 字节。
- HOOD logo 仅移除 `dpl` 参数的一次对照请求仍为 429；不对其他 logo 继续循环请求。
- 原始探测状态、类型和字节数保存在 `search-image-http-probes-20261011.json`；不记录代理信息和失败 HTML。
- 下载脚本成功保存 4 面真实原图国旗。下载清单区分 1 个实际失败 logo 探测与 20 个因同源 429 而未尝试的 logo，不能把未尝试项当作实际 HTTP 失败或已完成素材。

## 文件和复用

- 脚本：`scripts/download-search-images-fiscal-ai-7ee12bc9-company--NASDAQ_HOOD-4314f457-20261011.mjs`。
- 素材：`public/sites/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/search-images-20261011/`。
- 映射、内容类型、字节数和 SHA-256：`search-image-download-manifest-20261011.json`。
- 脚本可从任意当前目录运行；输出根目录根据脚本自身位置定位。此次已记录的 429 探测作为熔断依据，不重复 logo 请求。后续若有新的可下载来源或限流已解除证据，需要在新采样记录中明确更新依据，不能宣称现有 21 个 logo 已下载。
- HTTP 下载途径仍未取得真实 logo；不以文字、其他网站图标或生成图片替代来源 logo。

## 已加载资源缓存恢复

- 主浏览器已加载图片，通过 `Page.getResourceContent` 将原始图片内容保存到 `cached-hood-logo-20261011.json`、`cached-search-logos-batch-*-20261011.json` 和 `cached-search-logo-*-20261011.json`。该途径读取已加载资源，不重新请求受到 429 限制的 URL。
- 新脚本 `scripts/decode-search-image-cache-fiscal-ai-7ee12bc9-company--NASDAQ_HOOD-4314f457-20261011.mjs` 仅处理这些落盘文件：校验来源 URL 属于原清单、严格 base64、PNG/JPEG 签名及已记录 MIME，直接保存原字节，不转换或重画。
- 缓存恢复结果、来源文件、SHA-256、路径和仍缺 logo 清单写入 `search-image-cache-manifest-20261011.json`。原 HTTP 失败记录完整保留；新的成功不能抹去旧途径失败。
- 命名为 `search-images-20261011/logo-{ticker}.png` 或 `.jpg`，扩展名由真实内容确认；脚本重跑发现新 batch 并重建完整缓存清单。
- 首批 HOOD、QQQ、VTS、SPCX、META 共 5 个 logo 已恢复，签名、文件 SHA-256、系统图片解码及尺寸验证通过；后续 batch 以缓存清单为准，不能提前宣称全部素材完成。
- 最终本清单中的 21 个真实 logo 全部恢复、0 个失败、缺失 URL 数为 0；与前述 4 面国旗合计 25 个原图。该完成范围仅指 `search-live-images-20261011.json` 的素材，不代表完整搜索组件或所有动态结果已经完成。
- 公共采样页面已证明为 `https://fiscal.ai/company/NASDAQ_HOOD/`，记录在缓存 manifest 的 `observationURL`；新 raw 文件提供的 `sourceFrameURL` 逐项保留，早期 raw 未提供此字段的项仍为 `null`，不伪造逐项原始字段。
- 最终验证报告 `search-image-validation-20261011.json`：21 个 PNG/JPEG 通过真实系统图片解码及尺寸读取，4 个 SVG 通过 XML 解析；所有 25 个文件字节数和 SHA-256 与各自 manifest 一致。
- JPEG：VTI、QQQ、VTS、VOO、2222、IVV、SPY、VUG、AGTH.X、BOVB11、PIBB11；PNG：HOOD、NVDA、AAPL、GOOG、MSFT、AMZN、SPCX、TSM、META、AVGO。已观察图源中的巴西 It Now 素材 URL 明确为 `ticker=PIBB11`；没有下载或创建 `logo-BOVV11.jpg`。后续列表应按实际观察到的图片 URL 关联，不能仅凭行显示 ticker 猜测或重命名图源。
