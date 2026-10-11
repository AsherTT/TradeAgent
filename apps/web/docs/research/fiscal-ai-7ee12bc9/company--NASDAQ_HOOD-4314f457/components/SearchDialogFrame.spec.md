# SearchDialogFrame.spec.md — 2026-10-11
来源 https://fiscal.ai/company/NASDAQ_HOOD/；只负责有界搜索弹窗父布局，不是整公司页面。
证据：search-mobile-fresh-shell-20261011.json，search-mobile-investors-complete-20261011.json（182全节点），search-shell-all-computed-20261011.json，完整desktop630-node归档与tablet-search-shell-resumed。
源截图：source-{desktop,mobile}-search-investors-full-20261011.jpg。
现有labs的用户反馈授权修正该路由；不改变正式/app、首页、后端、真实.env。
## 合同与装配
named client SearchDialogFrame({children,onClose,header,footer})；header/children/footer为ReactNode。
header占42px搜索输入槽，children占完整results Card槽（由父提供），footer复用来源SearchGuidance。
这里实现section role=dialog aria-modal=true aria-label使用useLanguage("Search")，tabIndex=-1；body>column>close>search-block>footer。
只能写 SearchDialogFrame.tsx/module.css，不写输入/分类/结果/路由/数据；父负责状态和真实语义。
一个关闭目标，原X SVG真实路径从归档4节点提取到JSX，不用Lucide不同笔画。
body padding5，column padding12，flex column、overflowhidden、height100%。search-block flex1 1 0% minheight0，mb12，column方向。
search-block里面relative wrapper、stack column gap12；header form margin-bottom8（父负责），children Card margin-top10（父负责）。总间隔30。
desktop modal width1000 max-width100%，radius24，bg28/28/33，padding0 margin0，max-height90dvh overflowauto；自然body843.6px（1000高时）；不硬写该总高度。
fullscreen手机390和tablet768：modal width100% height100dvh，max-heightnone，radius0；body自然height，不能把column伸到整个viewport让results变高。
已实测768/390铺满，1440居中；1024切换点在适配暂定，需要父补核临界；不宣布所有断点验收。
outer fixed inset0 z300；desktop flex center，padding5dvh 72px；fullscreen padding0 align-items:flex-start。
overlay fixed inset0 bg rgba(0,0,0,.3)，no backdrop-filter；outside点击是否关闭父继续核对，frame先提供onClose但不要凭空实现外侧动作。
源modal shadow rgba(0,0,0,.05) 0 1 3 0，rgba(0,0,0,.05) 0 36 28 -7，rgba(0,0,0,.04) 0 17 17 -7。
源font Jakarta40016/24.8 白色；scopedCSS，外部默认reset不能变span inline。父提供字体variables（Jakarta+Mono）。
## Close
button native typebutton34x34 minwidth/minheight34，displayflex center，positionrelative，padding0，border0，radius24，margin-bottom4、margin-leftauto，color249/248/246，transparent。
SVG viewBox0 0 15 15，fillnone，真实path fillcurrentColor+evenodd，尺寸23.8x23.8（70%）。
source close DOM与native click已核对，click关闭，源公司h1保留。
Escape来源已桌面/平板/手机观察；父统一监听Escape，frame无需重复事件监听。
focus-visible ring1.6px solid94/94/116 offset1.6、native active translateY1 源Mantine共用规则。hover具体按钮色父仍补核；不要猜hover背景。
源transitionopacity .2s,transform .2s ease记录；初始/exit位移未采，不造猜测动画、不宣称关闭动画完成。
## 约束与检查
读worktree AGENTS与Next本地docs。来源CSS Modules明确允许保持准确性/命名空间隔离；无inline styles、any、default exports。
最小语义适配记录：给原无标签close增加t("Close search")，不会增加source界面新文案。
typecheck通过，commit中文 feat: 还原Fiscal搜索弹窗父布局；只两文件，别加入临时foundation。
完整来源搜索allstates尚未完成，这是一份完整有界父布局spec，后续父采边界后纠偏。
