# FullSourceHome 规格

- 目标文件：src/components/sites/simplywall-st-1b042a47/product-a/FullSourceHome.tsx；路由 `/`。
- 基准：现有 `/references/simply-wall-st` 页面和 FULL_SOURCE_BASELINE_20261008.md。
- 参考页与首页共同使用 FullSourceHome 的同一组件序列，notice/brand为两个实际入口的差异；参考页默认来源品牌，保持原说明与HTML布局。
- DOM：SourceFrame.home-page → aside（同参考样式）→ SourceNavigation → main.home-content → SourceFooter。
- 正文无条件原样复用参考页的全部11组件，顺序完全相同，不添加业务演示替代原视频或改文字。
- 原 SourceNavigation/SourceFooter 增加 brand 参数，默认 source；首页传 tradeagent。只有品牌 logo 与对应链接变化。
- 预览说明：完整来源复刻预览；原站媒体、评价、功能及外链为参考材料；自有功能入口为工作台；标注 Simply Wall St 来源。
- 元数据：TradeAgent、自有favicon、noindex/nofollow；双语仍沿用 LanguageProvider。
- CSS：全部继承现有来源；不写新的页面样式。具体颜色、字体、布局与断点见已提取的来源规格，不估算替代。
- 状态和响应式：全部继承原组件，含 Research 点击标签、导航 hover/Escape/汉堡按钮、双语切换与原断点。
- 素材：全部已有命名空间图片/视频/字体；仅新增自有品牌SVG。不删旧组件或资产。
- SSR回归：比较正文完整HTML、11 section数量、来源媒体/链接、品牌替换和已有本地账户落点。
