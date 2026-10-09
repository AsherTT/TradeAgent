# 完整来源首页恢复计划

2026-10-08 用户最新确认覆盖之前六分区适配首页：以 http://127.0.0.1:3107/references/simply-wall-st 为完整基底，只替换自有品牌，恢复被删减分区。采用本项目 clone-website skill，不另外制作原创首页。

- 应用根：D:/桌面/ai-website-cloner-template；site-key simplywall-st-1b042a47；page-key root-8a5edab2。
- 明确批准替换 `/`；`/references/simply-wall-st` 保留原标识及原组件；账户、公司、研究、实验室路由全部保留。
- 新首页组合组件：src/components/sites/simplywall-st-1b042a47/product-a/FullSourceHome.tsx。原 EnhancedAHome 文件保留作迭代记录。
- 正文按参考顺序复用全部 11 个来源组件：Hero、Platform、Tracking、PortfolioAnalysis、Research、StockSearch、Discovery、SmartUpdates、Community、Testimonials、FinalCta；加原导航与页脚。没有重写、减少、替代正文内容。
- 品牌只更换导航/页脚 logo 与它们的首页链接；局部参数默认 source，保证参考页仍是原标识。favicon 沿用自有 TradeAgent。
- 全局字体、来源 CSS、断点、视频、图片、标签状态、原站链接全部沿用。保留与参考页同样位置/样式的短来源预览说明，明确原站评价/链接/功能展示是参考，不计作本产品业务交付；首页 noindex。
- 新证据命名空间：docs/design-references/simplywall-st-1b042a47/root-8a5edab2/full-source-20261008/。不覆盖历史截图。
- 建造前基线构建通过；logo 独立工作树建造；主控负责原组件组合和 SSR 同源完整性检查。
- 验证：主内容 DOM、分区顺序、媒体及外链与参考一致；自有品牌、注册/登录/工作台链接和 noindex；检查/构建，桌面/平板/手机实测。不得把还原已有参考页等同于整个原网站或三个网站均已 1:1 验收。
- R1 code-review 继续原有 Standards/Spec 双轴流程，只定向审查本次差异，不再启动整套阶段审查。

完整首页视觉保留与首版研究平台后端范围分别记录；组合/筛选/社区的画面恢复不等于对应后台已实现。源站地址、评价、应用商店、法律主体不改写成 TradeAgent 的真实资料。素材及字体的公开上线使用权仍属 R6 待办，换 logo 不构成权利核验结论。

## 本次验证结果

- 新logo提交 b0f934a；完整装配/SSR提交61cdc1b；lint/typecheck/build通过，全部17项行为检查通过，无skip。
- 默认/无效/zh/en偏好下正文SSR与参考完整HTML完全一致，11个正文section，无删减媒体/控件；自有两logo及默认来源品牌隔离、账户入口和noindex通过。
- 实际1440/768/390的全部正文分区宽/高/相对位置（容差0.01px）、padding/display及logo尺寸与参考一致。viewport-parity.json保留原始实测；手机1px舍入溢出在参考同样存在，无新增。
- 桌面完整截图、平板/手机首屏对照已查看；67张图片全部加载（正文58张）、1个原视频。媒体动画帧随采样时刻变化。八个Research标签、移动菜单、English/Escape通过，interaction-checks.json记录结果。
- 保留来源说明是预览差异，手机104px，相比原参考84px多20px；正文内部布局不变。仅对所选本地参考完成本次对照，未宣称原网站所有页面/状态及三来源整站1:1已验收。
- 同一R1 code-review Standards/Spec代理定向复核 fff71bd...61cdc1b，均0新增发现；未重复启动阶段审查。现有账户/公司/研究流程保留，后台范围不扩张。
