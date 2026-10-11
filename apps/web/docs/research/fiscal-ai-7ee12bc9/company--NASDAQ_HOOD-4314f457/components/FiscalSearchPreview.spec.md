# FiscalSearchPreview 父装配纠偏规格 — 2026-10-11

本文件替代2026-10-10的三个静态叶子验证容器规格。用户指出孤立演示廉价、要求按本地clone工作流还原，授权更新现有lab。正式/app及首页保留。

范围：采集的完整弹窗外框、输入、分类、默认30条真实公开参考结果、投资者分类、提示，以及2026-10-12接入的九公司331个上市地点。结果数据/素材按SearchResultData、SearchResultRow与SearchListingRows规格；输入分类按SearchControls；父框按SearchDialogFrame。来源公司整页、页面搜索47行及全球搜索服务仍待，不能标R1完成。

父card：height65vh、widthfull、margin-top10、bg44/44/53、radius8、原三层shadow；frame stackgap12、formmb8，使输入下边到card上边30px。类别strip来源flexwrap，divider0.8px rgb64/64/79；结果滚动区域flex1/min-height0。默认30条按来源排序，10公司10ETF10投资者。源当前有历史HOOD Recent，但无历史的参考预览不伪造账户历史。

客户端初始open=true、query空、category=all、activeIndex0；close与Escape关闭，reopen保留query/category。真实参考样本匹配用名称和market字段，明确不冒充原站全球排名；不请求私有接口。category切换保留query并focusinput；ArrowUp/Down循环选择真实可见结果并scrollIntoView，Enter/点击仅确认参考选择与关闭，来源页面链接在关闭后提供。

空query原站Tab采样：保持inputfocus，清除active；实现forwardTab此状态，ShiftTab仍可到close。其他Tab页导航/47pages未装配，底部source tip保留比较，但外层明确待接入。escape提供退出；focus归还launch button；背景inert，dialog内Tab边界保持，body overflow开启期间锁定并恢复。

数据产品UI bilingual统一provider；证券名和ticker保留身份原文，分类/控制/提示/说明用t；切locale不resetquery/category。英文default source leaf保留原DOM/样式；EmptyMessage optional message、Guidance optional translate仅adapter。

外围只有紧凑说明、语言切换、重新打开和reference选择反馈，全部位于modal外，不能当source company背景。同宽截图比较modal/input/card/tab/list/row/footer真实rect/style，手机/平板fresh打开为fullviewport，桌面1000px居中。实际3width验收再纠偏，未观察的overlayclick/动画/Listing/导航不作全状态claim。

沿用R1已调用一次code-review的原两轴代理，仅本次新增diff定向复核，不重新启动整阶段审查。

来源使用叠加式自定义滚动条，不占列表内容宽度。父native滚动保留并隐藏内部gutter；自定义thumb拖动/hover/全状态尚待采集与装配，不标完整搜索验收。

## 2026-10-12 当前行为（覆盖上方历史待项）

referenceListings只含九家默认公司331个实测条目。筛选只匹配30条主结果name/market，不能用子上市代码搜索完整目录。展开可并存；保留仍可见公司的状态，被筛选移除后重现为折叠。lab选择子行只显示公司名、该market与真实来源链接并关闭，不写数据库。关闭/切语言/重开保留query/category/展开，这是用户上下文约束的适配；原站重新打开会清空输入和展开。

原listbox/option/aria-activedescendant模型已改为命名region/原生链接/独立按钮，输入aria-controls及aria-describedby关联结果和隐藏键盘说明，方向键目标由role=status播报。Tab空query清除高亮但允许自然前进至分类与链接；上方“保持输入focus”的来源记录保留为采样历史，不再作为当前实现要求。ArrowUp/Down仍只针对主结果，子行用原生Tab/Enter。此项为可访问性适配，不声称来源键盘全状态1:1。
