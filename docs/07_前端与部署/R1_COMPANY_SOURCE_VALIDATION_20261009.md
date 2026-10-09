# R1 公司来源基准与更新时间表验证

2026-10-09，Asia/Shanghai。关联正式开发计划FE-02、FE-03、QA-01。本次只推进公司来源采样及一个静态组件，R1/P10尚未完成。

## 当前结果

继续在D:/桌面/ai-website-cloner-template开发；主仓后端和apps/web未改。前端013cc7a建立公司独立来源基准/类型/作用域，1aceffc合入更新时间表，1d99091修正验证页窄屏外侧留白造成的额外换行；中文提交，未push或部署。

来源https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple本轮公开默认页面可读，没有遇到机器人验证。实测1440/768/390宽度分别保存3967/3936/3747个元素及父节点关系、文字、属性、矩形和32项布局样式；不称全部计算样式。桌面/移动全页截图分别1440×8067、390×11010，已读图确认正文末尾和页脚；平板全页截图仍缺。

来源页面观察到的两份CSS仅作公开静态素材下载，保存原始与存储哈希及末尾空白规范化记录；没有HTTP抓取HTML或第三方业务API。复用已有Bureau字体，只复制3个公开图片素材，173个inline SVG保存为库存；统计/广告/脚本不进入产品。

## 组件与三尺寸

先写CompanyDataStatusTable.spec.md和共享基础，再通过小工作树实现。组件仅接文本props，原生四行两列表格，不读网络、账户或解析来源时间。独立/labs/r1-company-data-status明确为来源静态样本；未接到自有/app或创建完整Apple来源路由。

最终本地1440/768/390实测无横向页面溢出；h2为24/32/500，格内8×16，数据格1024以下13/19.5、以上14/21，组件内距768以下16、以上32；手机表头和记录恢复来源换行。首次额外外侧留白已修正、重建并刷新复验。原生边框量化导致表高约1px差；平板独立容器与来源整页外框仍有约8px宽差，保留为完整页装配验收项，不宣称像素逐点/整页验收通过。

工程最终lint/typecheck/production build通过；已有六份前端检查启用产品及参考SSR，31 passed、0 failed、0 skipped。后端未修改，未重复474项后端检查。

## 原R1流程新增差异复核

沿用既有code-review两轴代理，仅复核前端17d6599...1aceffc新增组件、types、作用域CSS和实验页，不重新调用整阶段审查。

| 轴线 | 结果 |
| --- | --- |
| Standards | 0项；符合严格TS、命名导出、Tailwind、移动优先，作用域不影响首页 |
| Spec | 0项；结构、文字props、静态交互和来源样本声明符合spec，完整pageBuildersReady仍false |

验证页外框纠偏由主代理三尺寸对照完成，不改变组件契约。审查结论与来源全状态/整页验收分开。

## 剩余问题与证据

公开See All Risk Checks可打开和关闭，保存14条检查的DOM/分块样式及1440×999截图；弹窗内部滚动/键盘/窄屏仍待补。来源检查不代表TradeAgent风险分析结果。

公司页随后出现注册/登录提示，关闭后可读公开概览；点击More details后的状态再出现提示，About文本展开并显示Show less。URL元数据仍为主概览，滚动/导航位置读取超时，不能登记锚点跳转已验证。门户Analysis仍被“Sign up to continue”限制；未采到其正文。两者均未遇到机器人验证，没有操作第三方注册、登录或接受条款。

公司默认三宽度采样解决了“完全没有有效公司样本”的旧阻塞；整页仍缺平板截图、滚动/hover/图表/展开/菜单/异常状态、所有章节spec/实现、完整源pathname及自有对象适配后对照。门户来源尺寸和其他页签仍缺。当前P10→R1→来源采样与独立组件实现；R2尚未启动。

前端证据根：docs/research/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140；详细三尺寸数据与截图索引见components/CompanyDataStatusTable.validation.md。门户限制在portfolio--demo-128b5e04/README.md记录。正式待办以DEVELOPMENT_PLAN.md为准。
