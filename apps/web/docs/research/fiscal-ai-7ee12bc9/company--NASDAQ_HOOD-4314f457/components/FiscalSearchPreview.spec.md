# FiscalSearchPreview 父装配纠偏规格 — 2026-10-11

本文件替代2026-10-10的三个静态叶子验证容器规格。用户指出孤立演示廉价、要求按本地clone工作流还原，授权更新现有lab。正式/app及首页保留。

范围：采集的完整弹窗外框、输入、分类、默认30条真实公开参考结果、投资者分类、提示。结果数据/素材按SearchResultData与SearchResultRow规格；输入分类按SearchControls；父框按SearchDialogFrame。来源公司整页、页面搜索47行、Listing展开及全球搜索服务仍待，不能标R1完成。

父card：height65vh、widthfull、margin-top10、bg44/44/53、radius8、原三层shadow；frame stackgap12、formmb8，使输入下边到card上边30px。类别strip来源flexwrap，divider0.8px rgb64/64/79；结果滚动区域flex1/min-height0。默认30条按来源排序，10公司10ETF10投资者。源当前有历史HOOD Recent，但无历史的参考预览不伪造账户历史。

客户端初始open=true、query空、category=all、activeIndex0；close与Escape关闭，reopen保留query/category。真实参考样本匹配用名称和market字段，明确不冒充原站全球排名；不请求私有接口。category切换保留query并focusinput；ArrowUp/Down循环选择真实可见结果并scrollIntoView，Enter/点击仅确认参考选择与关闭，来源页面链接在关闭后提供。

空query原站Tab采样：保持inputfocus，清除active；实现forwardTab此状态，ShiftTab仍可到close。其他Tab页导航/47pages未装配，底部source tip保留比较，但外层明确待接入。escape提供退出；focus归还launch button；背景inert，dialog内Tab边界保持，body overflow开启期间锁定并恢复。

数据产品UI bilingual统一provider；证券名和ticker保留身份原文，分类/控制/提示/说明用t；切locale不resetquery/category。英文default source leaf保留原DOM/样式；EmptyMessage optional message、Guidance optional translate仅adapter。

外围只有紧凑说明、语言切换、重新打开和reference选择反馈，全部位于modal外，不能当source company背景。同宽截图比较modal/input/card/tab/list/row/footer真实rect/style，手机/平板fresh打开为fullviewport，桌面1000px居中。实际3width验收再纠偏，未观察的overlayclick/动画/Listing/导航不作全状态claim。

沿用R1已调用一次code-review的原两轴代理，仅本次新增diff定向复核，不重新启动整阶段审查。

来源使用叠加式自定义滚动条，不占列表内容宽度。父native滚动保留并隐藏内部gutter；自定义thumb拖动/hover/全状态尚待采集与装配，不标完整搜索验收。
