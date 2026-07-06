# EnterpriseMind RAG：企业知识库智能检索与可信问答平台

## 1. 简历项目经历版本

**项目名称：** EnterpriseMind RAG：企业知识库智能检索与可信问答平台

**项目描述：** 面向企业内部制度、合同、操作手册、会议纪要、产品文档等知识资产分散、格式复杂、检索低效、答案不可追溯的问题，构建一套企业知识库 Agentic RAG 问答系统。系统支持多格式文档上传、异步解析入库、混合检索、二阶段重排、引用溯源、权限隔离、评测追踪与低置信度兜底，帮助用户基于企业私有知识获得可信、可解释、可追踪的问答结果。

**技术栈：** Python、FastAPI、LangGraph、LangChain / LlamaIndex、Milvus、Elasticsearch / BM25、Redis、Celery、PostgreSQL、MinerU / Docling、Qwen3-Embedding、Qwen3-Reranker / BGE-Reranker、RAGAS、Phoenix、OpenTelemetry、SSE / WebSocket、MCP。

## 2. 项目亮点

- **异步文档入库流水线：** 基于 FastAPI + Celery + Redis 构建上传、解析、清洗、切分、向量化、索引构建的异步任务流，将耗时的文档处理从请求链路中解耦；支持大文件后台处理、任务进度追踪、失败重试和状态回查，避免上传接口长时间阻塞，提升系统并发处理能力。

- **复杂文档结构化解析：** 引入 MinerU / Docling 处理 PDF、Word、PPT、Excel、图片等复杂企业资料，将非结构化文档转换为 LLM-ready Markdown / JSON，并保留标题、页码、表格、图片说明、章节层级和阅读顺序；针对扫描件或表格密集文档启用 OCR / 版面分析，减少文本抽取错误对后续召回质量的影响。

- **多粒度分块策略：** 设计“结构化分块 + 语义分块 + Parent-Child Chunk”混合切分方案，先按标题、章节、表格、列表等结构边界生成父节点，再按语义完整性生成子 chunk；在检索时用子 chunk 精确命中问题，用父节点补充上下文，降低传统固定长度切分造成的语义断裂和表格错位问题。

- **Contextual Retrieval 增强召回：** 参考 Anthropic Contextual Retrieval 思路，为每个 chunk 生成 50-100 token 左右的上下文前缀，说明该片段在原文中的章节、对象、时间、制度范围或业务含义，再同时写入向量索引和 BM25 索引；缓解 chunk 脱离原文后缺少上下文、无法被准确召回的问题。Anthropic 官方实验显示，Contextual Embeddings + Contextual BM25 可降低 top-20 检索失败率，叠加 rerank 后效果进一步提升。

- **Dense + Sparse 混合检索：** 基于 Milvus 构建 Dense + Sparse 多向量检索体系，结合语义向量召回、BM25 精确匹配、RRF 融合排序和 Qwen3 / BGE Reranker 二阶段重排；既能处理“离职证明怎么开”这类语义问题，也能命中“TS-999、HR-2026-04、报销制度第 12 条”等编号、术语、条款类精确查询，提高中文企业知识库的召回稳定性。

- **Agentic RAG 工作流：** 基于 LangGraph 将一次问答拆分为意图识别、查询改写、多路召回、证据评分、低置信度补检索、答案生成、事实校验、拒答兜底等节点；当首轮检索证据不足时，Agent 自动改写问题、扩大召回范围或追问用户，使系统从“一次性向量检索”升级为可观测、可回退的多步检索推理流程。

- **GraphRAG / LightRAG 关系增强：** 引入 LightRAG / GraphRAG 思路，从企业文档中抽取部门、岗位、制度、流程、系统、负责人、审批节点等实体及关系，构建轻量知识图谱；面对“某岗位入职到转正涉及哪些制度和审批人”这类跨文档、多跳关系问题时，先通过图谱定位实体关系，再结合向量检索补充原文证据。

- **Grounded Answer 可信回答：** 设计基于证据的回答约束，要求模型只使用召回片段生成答案，并返回来源文档、页码、命中片段、相关性分数、引用编号和检索链路；当证据不足、来源冲突或命中分数过低时，触发拒答、澄清或人工确认，降低模型脱离企业知识库自由发挥导致的幻觉。

- **评测与可观测闭环：** 基于 RAGAS + Phoenix + OpenTelemetry 建立 RAG 质量评估与链路追踪体系，记录 query rewrite、召回节点、rerank 分数、上下文、token、耗时和最终答案；用 Context Precision、Context Recall、Faithfulness、Answer Accuracy 等指标对不同切分策略、embedding 模型、reranker 和 prompt 版本做 A/B 对照实验，避免“凭感觉调参”。

- **企业权限、安全与集成：** 面向多部门企业知识库设计租户、部门、角色、文档级 ACL 过滤，在检索前后都执行权限校验，避免越权召回；结合 OWASP LLM 风险点处理 Prompt Injection、RAG 污染、敏感信息泄露、供应链依赖和不安全输出；预留 MCP 接口，将企业知识库封装为标准化数据工具，便于后续接入 ChatGPT、内部 Agent 或办公系统。

## 3. 面试可讲版本

### 3.1 为什么不用单纯向量检索？

单纯向量检索适合语义相近的问题，但企业知识库里有大量编号、制度条款、部门名称、系统字段和专有名词。比如用户问“HR-2026-04 第 12 条是什么”，纯向量可能召回“报销制度相关内容”，但不一定命中精确条款。所以我会把向量检索和 BM25 / 稀疏检索结合，再用 RRF 融合和 reranker 重排，让系统同时具备语义理解和关键词精确匹配能力。

### 3.2 为什么要 BM25 + 向量 + Reranker？

BM25 负责精确词、编号、条款命中；向量检索负责同义表达和语义泛化；reranker 负责在初筛结果里做更细粒度的相关性排序。这个链路相当于“召回尽量全，排序尽量准”，比直接取向量 top-k 更适合企业文档问答。尤其在中文场景下，用户表达和制度原文经常不一致，混合检索能明显提升结果稳定性。

### 3.3 Contextual Retrieval 解决了什么问题？

传统 RAG 切 chunk 后，每个片段会丢失它在原文中的上下文，比如“本流程适用于正式员工”这一句单独拿出来，不知道是哪家公司、哪个制度、哪个章节。Contextual Retrieval 会给每个 chunk 增加一段短上下文，说明它来自哪份文档、哪个章节、讨论什么对象，再把这段上下文一起用于 embedding 和 BM25 索引。这样检索时更容易命中正确片段，生成答案时也更容易引用准确来源。

### 3.4 Agentic RAG 和普通 RAG 的区别是什么？

普通 RAG 通常是“用户问题 -> 检索 top-k -> 生成答案”，流程固定，检索失败时系统也可能硬答。Agentic RAG 会把问答拆成多个可控节点，比如判断是否需要检索、改写查询、多路召回、评估证据是否足够、必要时补检索或拒答。它的优势是可调试、可观测、可回退，更接近生产系统，而不是一次性的 demo。

### 3.5 GraphRAG / LightRAG 适合什么问题？

GraphRAG / LightRAG 更适合跨文档、多实体、多跳关系问题。比如“某个岗位从入职到转正涉及哪些制度、系统和审批节点”，单纯向量检索可能召回很多零散片段，但图谱能先定位岗位、流程、部门、审批人之间的关系，再补充原文证据。它不一定替代向量检索，而是作为关系推理和全局结构理解的增强层。

### 3.6 RAGAS 评估指标怎么落到工程里？

我会先构造一批企业知识库标准问答集，包括答案、来源文档和期望命中片段。每次调整切分策略、embedding 模型、reranker 或 prompt 后，跑同一批问题，用 RAGAS 统计 Context Precision、Context Recall、Faithfulness、Answer Accuracy 等指标。这样能判断改动到底提升了召回质量、答案忠实度，还是只是主观上看起来更好。

### 3.7 如何判断答案是不是幻觉？

我会从三个层面判断：第一，看答案中的关键结论是否能在召回片段中找到直接证据；第二，看引用来源、页码和片段是否匹配答案；第三，用 faithfulness / groundedness 评估模型检查回答是否超出证据范围。如果证据不足，就不让模型强行回答，而是返回“当前知识库未找到明确依据”或提示用户补充问题。

### 3.8 企业知识库怎么做权限隔离？

权限不能只在前端控制，也不能只在答案生成后过滤。我会在文档入库时记录租户、部门、角色、密级、可见范围等 metadata；检索前根据用户身份构造过滤条件，只召回用户有权限看的文档；生成答案时再检查引用片段是否都在权限范围内。这样可以避免向量库把无权限文档召回到上下文里，导致敏感信息泄露。

### 3.9 大文件上传和解析为什么要异步？

企业文档经常是几十 MB 的 PDF、PPT 或扫描件，解析、OCR、切分、向量化都比较耗时。如果放在同步接口里，用户上传会一直等待，接口也容易超时。异步任务队列可以让上传接口快速返回任务 ID，后台慢慢处理，并通过状态接口或 WebSocket / SSE 展示进度。失败时也能针对单个阶段重试，而不是整个流程重来。

### 3.10 如果检索结果不准，你会怎么排查？

我会按链路分层排查：先看文档解析是否丢表格、丢标题、页码错乱；再看 chunk 是否切断了语义；然后看 query rewrite 是否改坏了问题；接着看 BM25、向量召回和 reranker 各自的 top-k；最后看 prompt 是否正确约束模型只基于证据回答。配合 Phoenix trace 可以看到每一步耗时、输入输出和召回片段，定位问题会比只看最终答案高效很多。

## 4. 可落地架构表达

### 4.1 文档入库链路

```text
用户上传文档
  -> FastAPI 接收文件并创建 ingestion_task
  -> Celery 后台任务
  -> MinerU / Docling 解析为 Markdown / JSON
  -> 清洗、结构识别、元数据抽取、权限标记
  -> 结构化分块 + 语义分块 + Parent-Child Chunk
  -> Contextual Retrieval 前缀生成
  -> Embedding / Sparse 表示生成
  -> 写入 Milvus、BM25 / Elasticsearch、PostgreSQL
  -> 返回入库状态、页码索引、引用映射
```

### 4.2 问答检索链路

```text
用户提问
  -> LangGraph 意图识别
  -> 查询改写 / 多查询扩展
  -> 权限过滤
  -> BM25 精确召回 + Dense Vector 语义召回 + GraphRAG 关系召回
  -> RRF 融合排序
  -> Qwen3 / BGE Reranker 二阶段重排
  -> 证据充分性判断
  -> Grounded Answer 生成
  -> 引用来源、页码、片段、分数返回
  -> Phoenix / OpenTelemetry 记录 trace
```

## 5. 简历压缩版

**EnterpriseMind RAG 企业知识库智能问答平台**

面向企业内部制度、合同、手册、会议纪要等多格式知识资料，构建基于 Agentic RAG 的可信问答系统。系统采用 FastAPI + Celery + Redis 实现异步文档入库，结合 MinerU / Docling 完成复杂 PDF 与 Office 文档结构化解析；通过 Contextual Retrieval、Milvus Dense + Sparse 混合检索、BM25、RRF 与 Qwen3 / BGE Reranker 提升中文企业术语、编号和条款类问题的召回稳定性；基于 LangGraph 编排查询改写、多路召回、证据评分、低置信度补检索与拒答兜底流程；引入 LightRAG / GraphRAG 进行实体关系建模，支持跨文档多跳问题；使用 RAGAS、Phoenix、OpenTelemetry 对召回质量、答案忠实度、耗时和 token 成本进行持续评估与可观测追踪，并通过文档级 ACL 与 OWASP LLM 风险防护保障企业知识安全。

## 6. 技术依据与参考资料

- [Anthropic Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)：提出 Contextual Embeddings、Contextual BM25 与 reranking 组合，强调 chunk 上下文对 RAG 召回质量的重要性。
- [HKUDS LightRAG](https://github.com/HKUDS/LightRAG)：开源图增强 RAG 方案，强调实体关系抽取、知识图谱检索、reranker、RAGAS 评估与追踪能力。
- [MinerU](https://github.com/opendatalab/MinerU)：将 PDF、Office、图片等复杂文档转换为 LLM-ready Markdown / JSON，适合 RAG 和 Agent 工作流。
- [Qwen3-Embedding](https://github.com/QwenLM/Qwen3-Embedding)：提供 embedding 与 reranker 模型，支持多语言、长文本、检索、代码检索和 instruction-aware 使用方式。
- [Milvus Multi-Vector Hybrid Search](https://milvus.io/docs/multi-vector-search.md)：支持 dense / sparse 多向量混合检索，适合语义检索、关键词检索和多模态检索融合。
- [RAGAS Metrics](https://docs.ragas.io/en/latest/concepts/metrics/)：提供 Context Precision、Context Recall、Faithfulness、Answer Accuracy 等 RAG 评测指标。
- [Arize Phoenix](https://arize.com/phoenix/)：开源 LLM tracing 与 evaluation 工具，支持 OpenTelemetry，用于追踪 prompts、retrievals、tool calls 和 outputs。
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)：总结 Prompt Injection、敏感信息泄露、不安全插件、供应链等 LLM 应用风险。
- [OpenAI MCP](https://developers.openai.com/api/docs/mcp)：MCP 正在成为扩展 AI 模型工具和知识能力的开放协议，可用于把企业知识库封装为标准化数据源。

