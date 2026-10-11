# SearchResultRow 来源规格（2026-10-11）

## 范围与证据
- 目标是完整搜索弹窗中的真实结果行；不是自制展示卡片，不复用 labs 的说明样式。
- 本文件记录已经核实的来源渲染；未采行为明确标记，父搜索契约由父规格补齐。
- 默认源：`v602-desktop-search-empty-part-{000,100,200,300,400,500,600}.json.gz`，完整630节点。
- 结果数据：`artifacts/SearchResultRows.source-20261011.json`，默认30行、HOOD30行，各10公司/10ETF/10投资者。
- 全枚举CSS/extra/rect/DOM/SVG/图片证据：`artifacts/SearchResultRow.css-evidence-20261011.json.gz`，sources按原文件名索引。
- 默认每行完整tree保留全局index/parent，不能把节点index当React key；使用href。
- HOOD全30行只有完整内容/href；三类代表行深采不能冒充其余27行已采全部CSS。

## DOM（按证据保留层次）
- 证券行：`a > div(body) > span(label) > div(row) > button(tabindex=-1,type=button) > span(inner) > span(label) > div(identity)`。
- identity包含logo wrapper和文字stack；文字stack依次为名称p、flag+代码flex。
- body另有description span；选中公司出现description flex(p提示+kbd Tab)。
- 公司有Listings时，a末尾另有`span(section)>div>p(Listings)+svg(polyline)`；无Listings不造占位标签。
- ETF没有Listings section，description span可为零高度；不得统一套成公司卡片。
- 投资者：`a>div(body)>span(label)>div(row)`，row内隐藏响应式avatar wrapper和文字column。
- 投资者文字column为名称p及类型p；HOOD查询类型为` (Investor)`，空query专用Investors样本类型为空。
- 来源a内嵌button是真实DOM；是否改为无嵌套的可访问激活结构须父规格明确记录适配，不能默默增加两个可聚焦目标。
- 图片、精确文字和Listings因数据而异；不统一截断、改写、翻译或推导未采字段。

## CSS（精确值，宽高以内容和父宽度计算）
- 字体`var(--font-fiscal-jakarta),sans-serif`；body/label继承链按源节点，不让全局重置改变span display/行高。
- a：display:flex，align-items:center，position:relative，box-sizing:border-box，radius4px，border0，白字，默认16px/24.8px、weight400。
- 公司/ETF a padding:`8px 10px`，margin0；投资者padding10px，默认十条均测得margin-bottom8px（源`last:mb-2`作用于各行父层），不能只给整列表末条或所有证券行加8px。
- a宽为父可用宽度，height:auto；966px宽观测：首选公司81.8px、普通证券61.1px、HOOD投资者69.6px。
- 空query专用Investors代表行高度48px，说明类型是否存在会改变自然高度；禁止统一固定行高。
- body:block、overflow:hidden；label:inline、14px/21.7px、weight400；description:block、12px/18.6px、色175/175/182、overflow:hidden。
- label内row:flex,row方向，align-items:center，gap12px；identity:flex-grow，flex row，align-items:center，gap12px。
- 证券button:block,width100%，padding0，border0，transparent，14px/16.1px；inner/label span为inline（不是通用Button flex样式）。
- logo外层32px宽；内层span28×28、mr4px、radius6px、overflow:hidden、z-index:-1；img28×28。
- logo源class为`hidden md:flex`，手机span display:none、外层0宽/0高；不能保留桌面头像空白。
- 名称stack:flex,column,gap0；桌面名称16px/24.8px、weight400；手机14px/20.3px，正常换行。
- 代码flex:center,gap4px；代码p14px/20.3px、weight400；公司flag wrapper18×18、border0.8px transparent、radius4；flag img16.4×16.4圆形absolute。
- ETF flag wrapper14×14、position:relative；flag img14×14圆形，不套公司18px ThemeIcon。
- 公司description flex：margin-top2px、桌面margin-left44px、手机margin-left0，gap6px，align-items:center；手机深采25节点不含桌面kbd Tab（桌面26节点），不得移动端补造该键帽。
- description p12px/16.8px、色175/175/182、opacity0.7；kbd字体10px/15.5px、weight700、padding0 4px、radius8px、背景94/94/116、色216/217/223、opacity0.6。
- Listings section:flex,center，margin-left12px；内部gap4px；Listings p12px/16.8px、weight500、white-space:nowrap。
- Listings SVG16×16、display:block、stroke currentColor、strokeWidth2、fill none；transition transform0.2s cubic-bezier(0.4,0,0.2,1)。
- 投资者avatar外层32px，内层28px+mr4px；文字avatar div28×28、min-width28px、radius6px、flex center、14px/21.7px；不生成img。
- 投资者avatar桌面可见手机隐藏；名称/类型桌面16px/24.8px、手机14px/20.3px；column正常换行，不合并两个p。
- 手机代表父宽317.375px时公司109px/ETF76.9px/投资者60.6px；这是desktop-dialog resize样本，不能当fresh-open手机父布局。
- 所有padding/margin/background/border/transform未列项以相应原节点computed+extra为准；extra明确保存short hands，禁止仅凭computed键名缺失误判outline不存在。

## SVG与媒体
- 原Listings SVG：`<svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="16" width="16"><polyline points="6 9 12 15 18 9"/></svg>`。
- 公司/ETF必须真实logo img；默认20个logo URL和20个flag URL在数据images中，不能替换首字母。
- HOOD公司logo原图256×256、HOOY ETF128×128；完整URL/currentSrc/natural尺寸在HOOD代表images和深采image中。
- 国旗attrs.src为next image w3840，深采实际currentSrc为w32；不要把优化URL参数误认为原始图片尺寸。
- 当前manifest的HOOD logo下载HTTP429，其余logo/flag未本地归档；localPath=null/archived=false准确保留。
- 图片成功归档后由父统一资产映射；不得凭空填localPath或以当前不存在图片宣称1:1完成。

## 状态与可操作契约
- 非选中默认background透明；data-active选中背景28/28/33。这是键盘/默认选中，不能与hover64/64/79合并。
- 空query Investors长标题取得真正hover=false→true：背景透明→64/64/79，其余取原state节点；首条仍为选中28/28/33。
- 该长标题focus=true/focusVisible=true且仍hover：outline1.6px solid94/94/116、offset1.6px，背景64/64/79。
- HOOD公司hover=true档背景64/64/79，但baseline也已hover；不宣称已取得公司非hover差值。ETF hover/focus、公司非hover focus仍待核对。
- 查询名称使用真实b子节点高亮（HOOY名称HOOD、投资者Hood）；不把整行加粗。具体文本切分以深采节点或补采为准。
- HOOD ArrowDown选中ASML，ArrowUp回HOOD，焦点留input；鼠标HOOD hover与ASML active可同时存在。
- HOOD Tab切`HOOD pages`显示47内部页；Enter选HOOD关闭搜索且同pathname。父负责query、selected、键盘、scrollIntoView、关闭和路由。
- 结果行href必须按原数据保留；跨pathname点击/Enter、Listings展开、页面模式返回键未由这些档案证明，父继续补采。
- 不新增证券API、虚构加载/失败状态、Clear All或来源账户操作。

## 验收与待核对
- Builder读取适用AGENTS和Next文档，隔离实现来源行与父弹窗；不要再交付三个叶组件作为完整搜索。
- 校验默认/HOOD各30行原顺序、文字、href、分类数、logo/flag及Listings差异；所有未采字段留显式缺项。
- 实际Next字体/客户端三尺寸检查，分别测active/hover/focus；只测截图不能证明键盘选择和滚动。
- 当前尚缺tablet代表全枚举行CSS、HOOD其余行深采、真实媒体归档，以及上述未观察行为；父补齐后才能声明完整全状态1:1。
- 本轮仅来源提取与规格整理，不重新启动阶段code-review。

## 2026-10-11 三尺寸装配纠偏
最新search-source-tablet-investor-css：768px原站name14/20.3、gap6、avatar20；logo显示28。1440pxname16/24.8、gap12、avatar28。原768字号/间距判断已纠正；1024作为目前有界适配断点，临界仍待补采。

## 2026-10-12 上市地点接线与可访问性适配

九家默认公司的331个原始上市地点已采集、归档、接入父组件；此前“Listings未观察/待”的记录仅是历史。SearchResultRow外层flex column gap10，主链接与disclosure按钮并列，避免来源嵌套交互。按钮aria-expanded/aria-controls与区域ID关联，16px箭头旋转；多个公司可同时展开。SearchListingRows规格管理子行与分隔线。

主公司国旗补齐原站object-fit:cover和居中裁切。Apple激活说明以实测+13 more为准。所有href/别名按来源保存，不推断证券身份。

结果父容器改为命名region，主行为原生链接，不使用option/aria-selected；移除输入框活动后代关系，通过隐藏说明/状态播报保留上下键快捷选择。空query Tab清除高亮并自然移动焦点，是相对原站的可访问性适配。源码检验和截图不等于整搜索服务验收。
