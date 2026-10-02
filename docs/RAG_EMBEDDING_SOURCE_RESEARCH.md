# RAG 向量来源与 384 维兼容性调研

调研日期：2026-10-02（Asia/Shanghai）。仅读取仓库代码与官方公开文档，未读取凭据、安装模型、调用付费推理或修改实现。文档规格不代表本账户的真实调用已通过。

## 结论

阿里云托管 `text-embedding-v4` **不支持 384 维**。已有 Qwen 对话 key 可能可以在同账户调用该 embedding 模型，但必须匹配地域、业务空间、访问范围和计费类型；现有固定 384 维的 HTTP provider 不能仅通过更改模型名兼容。

若要优先复用 Qwen 托管服务，建议正规迁移到 **512 维**，重新向量化语料并隔离旧索引。若必须保留现有 `vector(384)`，原生 384 维的本地 `paraphrase-multilingual-MiniLM-L12-v2` 可实施，但其短 token 窗口要求调整分块策略。两条路线均不能拿旧模型向量与新模型向量混查。不可截短托管结果或补零来伪造 384 维。

## 当前代码事实

- `backend/app/rag/embedding.py`：`EMBEDDING_DIMENSIONS=384`，POST `{base_url}/embeddings`，传 `model/input/dimensions`；批量最多 64 条，每条最多 1200 字符；响应要求同条数、合法 index、非零有限值且恰好 384 维。
- `backend/app/persistence/models.py`：RAG 向量列 `Vector(384)`；持久化与检索也检查固定维度。检索用 cosine distance，并以 `embedding_model` 过滤。
- `backend/app/config.py`：RAG endpoint/key/model 独立配置；Qwen 默认 base 是旧式 `https://dashscope.aliyuncs.com/compatible-mode/v1`。本次未读取本地配置值，不能判断实际 key 类型、模型权限或实际 endpoint。

## 托管 Qwen：正式规格

[阿里云国内同步 Embedding API](https://help.aliyun.com/zh/model-studio/text-embedding-synchronous-api) 列出 v4 支持维度为 **2048、1536、1024（默认）、768、512、256、128、64**，最多 10 条输入、每条 8192 tokens，支持包括中英在内 100+ 语言。其国内北京报价为每千输入 tokens 0.0005 元；免费额度有时间限制，不能假定现账户尚有余额。`64~2048` 概览写法不能覆盖详细接口的离散允许值，也不能推出 384 支持。

[国际同步 API](https://www.alibabacloud.com/help/en/model-studio/text-embedding-synchronous-api) 同样列出离散维度及 10 条上限，提供 OpenAI 兼容 `/compatible-mode/v1/embeddings` 和原生 DashScope 接口。原生接口可区分 query/document；兼容接口未提供同样的显式参数契约，不能把原生字段直接塞进兼容请求并声称生效。响应 index 必须用于恢复输入顺序。

[官方 Base URL 总览](https://www.alibabacloud.com/help/en/model-studio/base-url) 与上述接口现文档提供按业务空间/地域的地址，例如 `https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`。实际应使用该账户创建 API key 时给出的 API Host，不应凭猜测拼工作空间。旧式 endpoint 是否可用于该现有 key 应由 root 核实；本调研不宣称旧地址已停用。

[官方 API key 文档](https://www.alibabacloud.com/help/en/model-studio/get-api-key) 说明不同地域的 key/endpoint 不能跨地域使用；可限制可调用模型。旧 key 在安全升级后仍有效，Coding/Token Plan 有专用 key，与 pay-as-you-go key 不同。所以“Qwen 对话成功”不能证明 embedding 权限；同账户不必然需要新账户，也不应把对话额度或 Coding Plan 视作 embedding 免费额度。

## 路线 A：512 维托管服务（工程建议）

1. 选 `text-embedding-v4` 的原生支持维度 512，保持 float 输出；把 provider 配置、输入验证、DB 列、查询向量、测试与索引统一成同一维度，不能只改 Python 常量。
2. 先检查已有 RAG 数据与索引。以新列/索引或可恢复的迁移策略重建，重新计算每个 chunk 的向量；不能通过 SQL cast 重用 384 维旧向量。schema 调整、旧数据处理与切换由 root 实施并审查，本文不执行迁移。
3. provider 内将最多 64 条逻辑批拆为每组最多 10 条，严格校验每组完整性并按 index 合并；任何子调用失败不得写入不完整 batch。实际子调用均计入资源/重试预算。
4. provenance/model 标识至少包含源、模型、维度、版本和预处理策略，区分传给 API 的模型名与内部检索空间 ID。请求和语料必须用同一空间；持久化/检索仍保持 PIT、标的与权限过滤。
5. root 确认 key 权限、实际 API Host 和计费授权后，再用公开的中英短文本做有界真实探针（如 2 条，一次请求，无重复重试），核对 512 维、非零有限数、顺序及 usage。随后运行真实 PostgreSQL 写入/检索、跨语召回与误召回金例。接口成功只证明连接/结构，不能证明语义质量。

512 维是降低改动及存储量的选择，不是本项目效果已优于 256/768/1024 的结论；要通过当前研究文档的检索金例后才定资格。embedding 独立按输入量计费，本次没有产生这类调用费用。

## 路线 B：保留 384 维的本地多语 MiniLM

[发布者官方模型卡](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) 说明该模型输出原生 384 维，支持 50 语言，许可证 Apache-2.0。卡中的模型结构指定 **max_seq_length=128**、attention-mask-aware mean pooling；不能拿任意 transformer hidden state 或错误 pooling 代替。

这是可在本机执行的开源模型，无需推理账号或服务 key；模型下载、依赖和硬件开销仍需准备。本调研未证明本机已有缓存/依赖或速度足够。建议固定模型 revision 与依赖版本，保留许可证和来源，显式拒绝未知远程代码。

现有 1200 字符 chunk 不能保证在 128 token 内，尤其中文。应以该模型 tokenizer 分块并保留原文定位/引用信息，或明确拒绝超长文本；不能静默截掉尾部后把向量当成完整 chunk 表示。query 也应有长度边界。使用 sentence-transformers 的正式 encode 与模型声明 pooling，返回原生 384 维；cosine 路线的归一化规则固定并记入空间 ID。

这条路线保留 DB 维度，但仍需重算所有该模型语料、隔离其他 384 维模型的向量，并增加本地 provider 选择。官方“多语”或“语义搜索可用”不能替代 SEC 财务/新闻检索的中文问英文材料、数字/否定、混淆文档、PIT/权限过滤金例。

## 本地 Qwen 的补充边界

[Qwen 官方 Qwen3-Embedding-0.6B 模型卡](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) 另有开源本地路线：100+ 语言、32k context、支持 32–1024 的自定义输出维度和 MRL。此模型的本地维度契约不同于阿里云托管 v4；不能以本地支持任意维度为托管 API 的 384 维证据。官方 MRL 输出策略不等于随便截短任意模型，但仍需单独实现、固定 pooling/instruction、内存/性能验证与 384 维检索效果资格；本次不优先扩展第三条实现路线。

## 本次资格状态

没有 live embedding 成功或检索效果资格。可以立即实施路线 A 的正规维度迁移与批量控制，或路线 B 的原生本地 provider 与 token 分块；不能只把现有 Qwen key 复制到 RAG 配置后宣称可用。不得随机向量、哈希向量、补零或截短结果进入正式研究证据路径；fixture 成功不算真实语义检索通过。
