# CompanyDataStatusTable

2026-10-09，Asia/Shanghai。第一个有界静态组件；整页未就绪。

## 边界与结构

源地址：`https://simplywall.st/stocks/us/tech/nasdaq-aapl/apple`。
只实现 Company Analysis and Financial Data Status 的标题和第一张更新时间表。
不包含随后的 Data Sources、模型说明和分析师名单，保留它们为独立组件待办。
结构：section → h2；section → overflow-x-auto div → table → thead/tr/2 th + tbody/4 tr/2 td。
将文本和行作为 CompanyDataStatusContent 传入；组件自身不读取网络、不内置 Apple 数据、不读取账户。
数据更新列是来源文本，不擅自解析日期、补时区或声称是自有后台更新时间。

## 外观（实际计算样式）

样本：overview-desktop/tablet/mobile-bounded.json.gz；元素父子关系已保存。
桌面1440、平板768、移动390宽度均实际测量，不使用最初截断样本。
section背景rgb(33,33,33)，圆角12px；移动padding16px，768及以上32px。
使用现有BureauSans/BureauSerif本地字体；不更改首页的.sws-source规则。
h2：BureauSerif，24px/32px，500，白色，margin0。
滚动容器padding-top32px。table为w-full/table-auto/border-collapse。
thead背景rgb(26,26,26)，白色；th字体700；tbody字体400。
表格字号：1024以下13px/19.5px，1024及以上14px/21px。
所有th/td：padding8px 16px；第一列左对齐，第二列右对齐。
table/前三条数据行边框rgba(238,236,226,.1)；末行rgba(255,255,255,.05)。
来源CSS声明border-width1px，计算样式像素量化为0.837696px；保留声明1px，记录量化差异。
source-css/base.b3ff7a10.css明确1024断点修改--s-text-xs-size；main.41545de5.css确认md:p-x4为32px。

## 交互、状态、动画

INTERACTION MODEL: static，狭窄容器可原生横向滚动。
N/A：没有按钮、链接、hover样式、切换、轮询、加载、权限或动画。
响应式只改变section内距和表格字号；保留table，不转换为卡片。
所有四行在三个尺寸均可见。整页其他控件状态不属于该组件完成声明。

## 实际来源文字（只用于开发预览）

标题：Company Analysis and Financial Data Status。
列：Data；Last Updated (UTC time)。
Company Analysis → 2026/10/07 18:18。
End of Day Share Price → 2026/10/07 08:00。
Earnings → 2026/06/27。
Annual Earnings → 2025/09/27。

## 素材与截图

N/A：该表无图片、SVG或视频；仅复用已在shared/fonts保存的字体。
整页基准：docs/design-references/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/overview-desktop-full-calibrated.jpg 和 overview-mobile-full-calibrated.jpg。
先保存完整来源及表格范围截图，再完成本地三尺寸对照。

## 落点与验证

具名组件：src/components/sites/simplywall-st-1b042a47/stocks--us--tech--nasdaq-aapl--apple-eed85140/CompanyDataStatusTable.tsx。
只用Tailwind类，不使用inline style或any；两空格。
foundation在shared/company-foundation.css；字体变量由本地开发预览页面提供。
单独开发验证页/labs/r1-company-data-status，明确为来源静态样本；不是完整公司复刻路由，不接入/app。
verify tsc、lint、production build；本地1440/768/390核对字体、颜色、内距、表格语义和横向溢出。
