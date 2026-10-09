# EnhancedAHero：来源首屏结构适配

Target: src/components/sites/simplywall-st-1b042a47/product-a/EnhancedAHero.tsx
Source: https://simplywall.st/，HeroSection/HeroMedia；computed-full root1三尺寸；原CSS整体不变。
Screenshot: docs/design-references/simplywall-st-1b042a47/root-8a5edab2/source-desktop-1440-20261006.png及768/390。
DOM: section.home-hero > .wrap > .hero__content > .hero__text(h1/span.serif、p、.btn-row两按钮、caption) + 原heroMedia外层(div flex h575 min-w0 flex1 items-center justify-end)。不可另造grid/warmhero/roundedwhitecard。
精确CSS：home-hero #edebe1 padding60px0 64px；wrap原max1600/padding0 40px；hero__content flex aligncenter gap40px paddingtop40px；hero__text width540px flexnone column gap8px；h1 sans52px/57.2px weight400 marginbottom10px，span.serif bronze#986e2e；p sans18px/21.6px weight400 marginbottom10px；caption ui12px/20px #3a3226 paddingbottom10px。复用原class，响应式由source-styles原991/640规则：<=640h1 36px/40px，不添加新的1024断点替代原布局。
Text：中文“欢迎来到你的”+serif“公司研究中心。”；英文“Welcome to your”+serif“Company Research Center.”；段落中文“关注公司、阅读财务、追踪研究与核验证据——把公司、问题和来源连接在同一个空间。”；英文“Follow companies, read financials and trace research back to evidence — companies, questions and sources in one space.”。
CTA：原.btn.btn--gold“开始研究”/“Start research”→/app；原.btn.btn--black“查看产品演示”/“Explore the demo”→#demo，必须本地。caption“演示使用虚构数据，真实研究需登录。” / “Fictional demo data. Sign in for your own research.”。
原hero视频替换为用户已确认的可交互demo：media: ReactNode由页面装配注入（根代理完成）；保持原media槽位h575、width837/max100%、shadow rgba(0,0,0,.2) 0 24px32px5px。demo是明确适配差异，不复制原站portfolio视频。不放Trustpilot/7M/真实投资成绩。
Interaction: CTA锚点展示demo，本地提交链接仅导航，不自动提交。demo由另一组件维护，本文件不要实现mock/状态/复制demo。
Assets无需新增，源字体/颜色已共享并路由范围隔离。
Build：命名导出、2spaces、strict TS、Tailwind no inline styles；npx tsc --noEmit + npm run build。只修改目标文件，别改SourceHero/CSS/根layout/路由。
