# R1 公共应用壳增量验收 — 2026-10-12

FE-02/FE-03/QA-01 公共外框增量，代码 `e8c6e85`；来源冻结 `4dac702`，header/sidebar 分别 `bee3497`、`7828ebd`。本记录为验收证据，任务状态只维护 DEVELOPMENT_PLAN.md。

## 实际交付与流程

`/app/layout.tsx` 装配 Fiscal 来源顶栏、80px侧栏和移动全宽抽屉。门户、公司、研究、账户锚点均为自有地址；搜索是真实 SEC 目录 Link，`/` 快捷键进入该页。AccountShell 通过共享上下文移除旧全局 ProductHeader；各页面原认证/重定向、DTO、本人数据及业务正文保持。

按 [clone-website skill](../../apps/web/.agents/skills/clone-website/SKILL.md) 完成真实浏览器三尺寸/断点/抽屉/hover/shortcut来源采样、两份完整小spec、两个隔离worktree builder、每次合并build及产品接线复验。[产品规格](R1_APP_SHELL_SPEC_20261012.md) 与 [来源 namespace](../../apps/web/docs/research/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/) 保留完整证据。

门户正文、公司完整概览、研究列表/提交、任务与报告正文仍待逐页来源重构。目录页原正文内语言控件暂保留，后续正文统一时收拢；本轮外框不代表所有正文迁移或整站完成。搜索弹窗覆盖viewport，目录候选仍无关注或研究资格。

## 浏览器与来源对照

| 验证项 | 结果与边界 |
| --- | --- |
| 中英1440/768/390 × 1000 | 顶栏64px；1440左偏移80px/侧栏80px；768/390关闭抽屉隐藏；6种布局scrollWidth=clientWidth |
| 1023/1024 | 1023 burger显示/header left0；1024 sidebar80/header left80；打开抽屉进入桌面关闭、恢复overflow，focus转搜索Link |
| drawer | 打开focus close，背景header/content inert；Tab/ShiftTab循环；close/Escape返回burger、恢复原overflow；切语言不关抽屉 |
| 390×280短窗口 | 导航可视94px/内容204px独立纵滚；语言控件底264px在窗口内；真实Tab循环及Escape通过 |
| 导航/刷新/返回 | 抽屉研究链接关闭并显示Research active；SEC搜索→自有A公司详情；刷新身份/语言保留；返回搜索后drawer关闭、搜索自己的modal正常打开 |
| 编辑与shortcut | 研究输入KLAC/保留斜杠且不跳页，切语言保留字段；非编辑位置/进入SEC搜索并focus输入。修饰键/repeat/composition/modal保护有实际挂载测试 |
| 来源形状 | 英文桌面91个明确选定CSS值0差异；详见APP_SHELL_BOUNDED_COMPARISON_20261012.json。kbd18.8×27.8、搜索36高、sidebar80及label11/17.05匹配；不是全截图像素等同 |

原来源 Escape 不关闭抽屉，close后focus留在隐藏close；产品focus循环、Escape、背景inert、断点处理和原overflow恢复是明确无障碍适配。自有品牌槽、菜单数量、语言宽度及真实Link也为适配。字体沿用来源文件；搜索Link图标槽相对偏移约0.2px、父层继承行高24px（来源24.8px）、零宽border/reset和默认outline差异明确登记，不能把91项局部值推广成整页零差异。

默认截图以公开SEC身份页展示外框，不含私人账户正文：`local-app-shell-{en,zh}-{desktop,tablet,mobile}-20261012.png` 和mobile-open位于 [截图 namespace](../../apps/web/docs/design-references/fiscal-ai-7ee12bc9/company--NASDAQ_HOOD-4314f457/)。最终测量等待动画稳定并核对语言；早期中间帧和错误语言样本已覆写。

## 检查与审查

前端52项测试全通过（PRODUCT_PREVIEW_URL启用运行中SSR），lint/typecheck/build通过。新增3项实际挂载AppShell/AccountShell，验证shortcut编辑保护、抽屉焦点/滚动/断点/路由及语言字段保留，不以CSS镜像测试代替浏览器。首次缺AppShell测试为红；JSDOM无原生Tab默认移动，因此测试用明确focus准备边界，实际浏览器另验真实Tab。

新增layout曾使开发路由类型未同步，生成最新类型后typecheck通过。两个组件逐次合并build与最终接线build通过。后端无改动，未重复无变化全后端本地检查。

### Standards

固定新增diff `3ea0c3c...e8c6e85`，沿用本R1代理定向复核。0项硬性违规，0项需修改的smell；源CSS Modules/namespace及布局上下文用途符合约定，跳过工具强制项。

### Spec

同一固定diff，0项缺失/部分实现、0项scope creep、0项错误实现。公共壳、page auth保留、真实links、drawer/shortcut状态及来源样式符合三份小规格。此复核不代替浏览器或完整R1验收。

两轴总数均0，没有重复整个R1阶段审查。模型/worker/beat、采购、schema及部署未开启。R1未完成，R2未启动。下一块门户正文来源规格/关注/活动任务/最近研究/变化/目录→公司→研究列表/提交→任务状态/预算/取消→报告/引用及账户→R1整站验收，再依既定R2～R6/P11顺序推进。
