# SearchControls.spec.md — 2026-10-11
来源https://fiscal.ai/company/NASDAQ_HOOD/；有界搜索弹窗输入与分类栏，父负责结果/页面模式/后端。
来源文件search-mobile-investors-complete-20261011.json（182完整节点），search-mobile-fresh-shell-20261011.json，desktop630全节点，以及search-current-results-20261011.json。
共享基础字体变量Jakarta与Mono、SearchCategory类型已冻结。只写SearchInputBar.tsx/CSS Module、SearchCategoryBar.tsx/CSS Module。
## 输入（完整inline规格）
合同 named client SearchInputBar({query,onQueryChange,onKeyDown,inputRef,activeResultId})，RefObject<HTMLInputElement|null>，KeyboardEventHandler。
form role search、margin-bottom8、height42；onSubmit preventDefault；wrapper relativewidthfull。
input native type search、maxLength512、spellCheckfalse、autoCompleteoff、autoCapitalizeoff、autoCorrectoff、enterKeyHintgo。
id main-search-bar-modal；真实placeholder Search 50,000+ companies，现有t翻译；aria-label t("Search")。
query受控，onChange透传，不trim或locale reset；键盘委托父，不添加另一个clear/query状态。
width100%，height/minheight42，boxsizingborderbox；padding0 14px 0 40px，白色Jakarta40016/40px，letter-spacingnormal，bg44/44/53，radius32，border.8solid175/175/182，outline none，transition .2s ease-in-out。
源手机focus=true仍borderdim/boxshadnone；desktop早期focus记录border242/199/133，shadow rgba(242,199,133,.4) 0 0 15 3 / rgba(242,199,133,.8) 0 0 0 1。桌面focus真实再采父纠偏，不能宣称全focus已验收。
search icon left:absolute x0 y1 width40height40 flexcenter color175/175/182 pointer-eventsnone，svg18x18 stroke currentcolor2 fillnone viewBox0 0 24 24 circle11,11,r8 line21,21 to16.65,16.65 roundcap/join。
desktop>=1024 query空时右侧"/" kbd可见：源当前shell index20，从search-shell-all-computed-20261011.json枚举CSS及first-part属性取精确字体/边框/opacity；父补shorthand可读key CSS border各side。手机fresh无kbd，不补。
右hint出现input rightpadding40，否则14；原webkit native search cancel显示与否父以浏览器验证，先保留native type语义。
aria-autocomplete list，aria-controls fiscal-search-results，aria-activedescendant父activeResultId可空，不指向不存在元素。
## 分类栏（完整inline规格）
合同 named client SearchCategoryBar({category,onCategoryChange})；category enum all/company/etf/investor。
DOM flex wrapper margin10px0 10px12px，gap10；innerblockwidthauto>div role tablist flex flex-wrap gaprow4、column0。
4 native buttons role tab：All / Companies / ETFs & Funds / Investors，对应四category；onClick父回调；aria-selected；不改变form query。
button p0 border0 bgtransparent，margin-right4，fontJakarta40016/18.4，cursorpointer，displayblock。
button>span inline font16/18.4>div badge inline>span label inline；必须保留源inline linebox，不把badge变inline-flex；computedbadgeheight26但实际rect18.4高。
badge padding0 10px radius1000，font13/24px letter-spacing.25 uppercase overflowhidden。
unselected weight500,colorwhite,bgtransparent，border.8solid249/248/246；selectedweight600,colorblack,bgwhite，border.8transparent。
label inherit全部，inline、overflowhidden/textoverflowellipsis/nowrap。源labeltext大小写原始All但CSSuppercase展示ALL。
buttonfocus-visible源通用ring1.6solid94/94/116offset1.6，selected与hover不合并；未采专属hover背景不猜。
mobile356.4父宽，strip344.4w：前三标签一排，Investors第二排；tablist52px，总margin栏72；desktop/768一排24px，总栏44px；靠flexwrap自然，不写固定tablist高度。
来源categoryclick后input焦点保持；父在onCategoryChange后inputRef.focus，组件不要重复键盘监听。
## 约束
仅CSS Modules允许保持来源精确值，无global/inline styles/any/default exports；使用useLanguage，原证券名称不翻译。
必须typecheck，commit中文feat: 还原Fiscal搜索输入与分类控件，仅4文件；不要提交临时types、push、开server或调用review。
当前不作为全部来源键盘/hover/导航状态验收，父实际三尺寸对照后补齐。
