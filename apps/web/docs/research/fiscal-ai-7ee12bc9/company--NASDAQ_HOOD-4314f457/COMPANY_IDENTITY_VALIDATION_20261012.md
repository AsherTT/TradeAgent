# 公司身份/概览：严格clone流程纠正（2026-10-12）

用户再次要求执行模板skill后，明确撤回“通用功能目录详情可当作复刻”的做法。实际工作流为迁入主仓的[clone-website](../../../../.agents/skills/clone-website/SKILL.md)，来源仍为 https://fiscal.ai/company/NASDAQ_HOOD/。

## 流程与输出

- 先补输出计划、1440×900/768×1024/390×844的来源完整截图、可审计样式树与静态/展开/hover/focus行为，再写两个完整spec。
- 一个独立Git工作树的两个独立builder任务；每次只实现一个组件，提交前typecheck。管理工具无法在聊天父目录识别Git仓库，改用主仓Git原生worktree；未写主仓或混入其他模块。
- 身份builder0242d39合入e8eb4fa；概览builderbf7f85a合入89f02f4；每次合并后生产build通过。主代理对照修复列表包装、分隔线继承和验证容器宽度。
- 新建2组件、2spec；复用已有Jakarta字体和真实HOOD标识，新增一个提取的内联外链SVG，未额外下载素材。来源资产命名空间与源pathname未来整页输出保持。
- 来源子块 → `/labs/r1-fiscal-company-identity` 原文比较 → `/app/companies/discovery/{cik}` 真实SEC身份适配。搜索/API另见主方案，不将来源样本用于产品财务。

## 有界对照结果

见 [COMPANY_IDENTITY_COMPARISON_20261012.json](COMPANY_IDENTITY_COMPARISON_20261012.json)。比较身份首两个子树（logo/name/market，省去动作与报价兄弟）及概览内部47节点，不比较完整页位置。三尺寸共648几何值，0项超出0.05px容差，最大差异0.0125px。共2091条选定样式属性检查，有2条预期的计算后auto右边距差异：平板省去70px收藏/笔记、手机省去34px音频控件；名称/图标可见坐标、大小未改变。不是完整CSS/整页像素0差异声明。

字体用下载的同源TTF，编译后的Next字体别名不同，未冒称font-family字符串相同。展开使用局部CSS intrinsic sizing代替源站运行时数字高度，保持60px收起和200ms过渡；不支持intrinsic interpolation时为即时展开。内部实现差异和长字段换行保护均为显式适配。原文参照不与中文长度混算。

来源实测描述展开/收起、hover下划线、真实键盘焦点1.6px/offset1.6px，表格字段及全部5条分隔线；本地收起态三尺寸与原生Enter展开已复验。所有保存数据都包含实际viewport，尺寸不一致的临时读取不得作为同尺寸通过证据。完整商业页、导航、收藏/音频及价格图表没有因此完成。
