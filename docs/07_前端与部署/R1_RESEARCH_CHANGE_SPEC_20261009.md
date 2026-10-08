# R1 本人研究记录变化增量

日期：2026-10-09。接续正式计划 BE-01、FE-03，主仓固定点 da96256，前端固定点 edd38c5。沿用 implement、tdd 和既有 R1 双轴审查流程；只复核此次新增差异，不重复整阶段审查。

## 有界行为

公司详情 GET /workspace/companies/{instrument_id} 新增 research_change。仅比较当前账户、当前公司已持久化的 complete / insufficient_evidence 记录；失败、取消、活动任务不能作为研究变化。历史未归属记录不可见，不写业务状态，不调用模型或外部数据。

读取最近 50 条结束记录（created_at、ID 降序），与列表分页独立；读取第 51 条仅判断 has_more。公开 window_limit、has_more，不能宣称全历史。latest 为窗口内最新提交、具有时区有效分析截止时间的记录；previous 为其之前最近提交且分析截止时间严格早于 latest 的记录，须 query、horizon、timestamp_mode、replay_integrity_level、collection_only 全部相同。不得跨问题、期限、模式比较，或把同一截止时间重复采集说成时间变化。

无 latest 返回 no_finished_research；有 latest 无 previous 返回 no_comparable_previous；可比较返回 available。available 返回两份快照和 signed qualified_evidence_count_delta、evidence_gap_count_delta；其余 delta 为 null，不能用 0 冒充未知。快照仅含既有安全 ResearchSummary、analysis_timestamp、data_quality_status、quality_gate_decision、qualified_evidence_count 和 evidence_gap_count。证据数量复用 qualified_evidence 的公司、时间、来源准入规则，并按 evidence_id 去重；缺口只计持久化 evidence_gaps 去重数，不增加或展示内部正文/凭据。

以上是研究记录的覆盖与质量变化，不是公司评分、市场表现、预测准确率或投资结论。证据增加不自动代表质量改善；各记录 cutoff 可见，不宣称历史 PIT 来源资格。时间无时区的旧记录不参与。记录不足或窗口外可能有记录时显示原因。

## 账户界面

在现有公司联调页面增加“研究记录变化”自有业务区块，包含上下两次报告本地链接、问题/期限/采集模式、各分析时间、状态/质量/准入证据数/已记录缺口数以及两项差值，支持中英文及移动端。导航锚点到真实区块，加载/错误/401 沿用公司生命周期；失效会话清除全部比较内容。该区块不作为 Simply 来源复刻，不改已认可首页。门户入口复用公司链接，本轮不扩大聚合范围。

## 已认可测试边界与验收

沿用账户 HTTP、BFF、实际 React 页面公开边界；数据库仅用于离线 worker 检查点夹具准备，断言一律经 HTTP/页面读取。逐条 red→green：真实记录差值、来源准入/去重、缺失/不可比较/窗口范围/分页独立、账户和公司隔离、双语报告链接与401清除。普通后端完整测试及 Ruff/mypy，前端 lint/typecheck/build 与既有行为回归。离线夹具不计真实供应商资格；保留来源采样超时，BE-01 完成状态不扩展到公司财务/论点变化。

中文提交，仅本次文件，保留旧 dirty。不 push、部署、重置真实数据库或启用 worker。
