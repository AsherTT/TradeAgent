# 默认 / HOOD 结果 typed 来源数据规格（2026-10-11）

## 来源和计数
- 工件：`../artifacts/SearchResultRows.source-20261011.json`（相对本文件components目录）。
- schemaVersion=1；sourceSnapshotDate=2026-10-10，generatedDate=2026-10-11，不把本次提取日期当新来源采样日期。
- default来自连续完整630节点七分片；hood来自完整`v602-desktop-search-hood-content.json.gz`链接表。
- 两组均严格保留来源结果顺序：30行，10company/10etf/10investor。
- HOOD的`/products/mcp/`是辅助Learn more，在auxiliaryLinks，不放入30结果。
- `HOOD pages`47内部页面结果保留在原归档；不是本数据的company/etf/investor结果集合。

## TypeScript数据合同（规格，不是产品源码）
```ts
type ResultKind = "company" | "etf" | "investor";
type EvidenceRef = { file?: string; files?: string[]; index?: number; href?: string };
type ImageEvidence = {
  sourceURL: string; alt: string; localPath: null; archived: false;
  currentSrc?: string; naturalWidth?: number; naturalHeight?: number;
};
type SourceNode = {
  index: number; parent: number; tag: string;
  attrs: Record<string, string>; text: string;
  rect: Record<string, number>; styles: Record<string, string>; svg?: string;
};
type BaseResult = {
  kind: ResultKind; href: string; name: string; avatarText: string | null;
  description: string | null; listingsText: string | null;
  images: ImageEvidence[]; sourceRef: EvidenceRef;
};
type DefaultResult = BaseResult & {
  marketRaw: string | null; marketTickerChildren: string[];
  investorType: string | null;
  textFragments: {index:number;parent:number;tag:string;text:string}[];
  tree: SourceNode[];
};
type HoodResult = BaseResult & {
  sourceText: string; marketText: string | null;
  representativeDeepRef: EvidenceRef | null;
  assetStatus: "not-applicable" | "URL-known-unarchived" | "URL-not-captured-in-this-artifact";
};
type SearchResultSource = {
  schemaVersion: 1; sourceURL: string; sourceSnapshotDate: string; generatedDate: string;
  notes: string[]; default: DefaultResult[]; hood: HoodResult[];
  auxiliaryLinks: {href:string;text:string;selected:unknown;rect:Record<string,number>;background:string}[];
};
```

## 消费规则与完整度
- href是原始字符串，保留末尾斜杠、大小写、点号及括号；不得擅自normalize或改成虚构本地公司路由。
- default.tree包含原行全部后代、精选CSS、SVG；全局parent不重新编号。脱离原树使用时root.parent可在tree之外，这是正确来源。
- 默认text只保存直接文本，不能递归简单拼接并声称等于DOM textContent；ETF ticker是p的内嵌span。
- 如marketRaw=`ARCA:  (ETF)`、marketTickerChildren=[`VTI`]，ticker应插在冒号后类型前；其余文字/空格以原节点及实时核对为准。
- default.name/description/listingsText/avatarText均读取对应源节点；证券无avatarText，投资者无证券图片。
- HOOD sourceText为原档完整textContent，是权威字段；name/marketText/description/listingsText从其明确分界提取，不是API返回。
- HOOD投资者sourceText包含前两位avatar与末尾` (Investor)`；name移除这两项，avatarText另存。
- b高亮切分只在三代表深采可核实；不能从name字段假装其余行已保存富文本结构。
- 默认20证券logo/flag URL全，均未归档；HOOD仅HOOD/HOOY代表媒体URL完整，另外18证券行媒体显式未采。
- images=[]不能默认解释为“无logo”：证券必须检查assetStatus；投资者not-applicable才是无img。
- localPath=null/archived=false是当前来源档案状态；成功归档后另做版本化映射，不篡改此证据快照。
- 此数据是两个已观察query快照；任意输入的匹配/ranking、近期历史和完整搜索服务不能由数组filter伪装成来源实现。
- 父搜索规格补充最新Recent、分类切换、47pages和其他已采query的精确状态，不从旧快照覆盖当前来源历史。
- Builder可生成typed产品数据，但必须保留来源trace并复核30/30、各10/10/10、href唯一及无辅助链接混入。
