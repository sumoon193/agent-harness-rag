"""
FastAPI 依赖注入。

组装所有 service 实例，供路由层注入。
- fallback 模式：全部使用 in-memory / fake 实现。
- full 模式：接入真实外部服务（PostgreSQL / MinIO / Milvus / ES / Redis）。
"""
from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.schemas.enums import ToolRiskLevel
from app.schemas.tool import ToolDefinition
from app.services.agent.approval_manager import ApprovalManager
from app.services.agent.artifact_timeline import ArtifactTimelineBuilder
from app.services.agent.run_manager import AgentRunManager
from app.services.agent.step_logger import StepLogger
from app.services.agent.tool_executor import ToolExecutor
from app.services.agent.tool_registry import ToolRegistry
from app.services.agent.tools.clarification import ClarificationHandler
from app.services.agent.tools.hr_checklist import HRChecklistHandler
from app.services.agent.tools.mock_ticket import MockTicketHandler
from app.services.agent.tools.policy_search import PolicySearchHandler
from app.services.agent.tools.user_profile import UserProfileHandler
from app.services.answer.grounded_answer import FakeAnswerGenerator, GroundedAnswerService
from app.services.evaluation.eval_runner import EvalRunner
from app.services.retrieval.embedding.base import Embedder
from app.services.retrieval.reranker.base import Reranker
from app.services.security.acl_validator import ACLValidator


def _build_tool_registry() -> ToolRegistry:
    """注册 V1 五个工具。"""
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="policy_search",
            description="检索 HR 制度文档",
            permission_scope="hr.document.read",
            risk_level=ToolRiskLevel.READ,
            requires_approval=False,
        ),
        PolicySearchHandler(),
    )

    registry.register(
        ToolDefinition(
            name="user_profile",
            description="查询用户档案",
            permission_scope="hr.profile.read",
            risk_level=ToolRiskLevel.READ,
            requires_approval=False,
        ),
        UserProfileHandler(),
    )

    registry.register(
        ToolDefinition(
            name="hr_checklist",
            description="获取 HR 流程清单",
            permission_scope="hr.checklist.read",
            risk_level=ToolRiskLevel.READ,
            requires_approval=False,
        ),
        HRChecklistHandler(),
    )

    registry.register(
        ToolDefinition(
            name="clarification",
            description="请求用户澄清",
            permission_scope="hr.chat.write",
            risk_level=ToolRiskLevel.READ,
            requires_approval=False,
        ),
        ClarificationHandler(),
    )

    registry.register(
        ToolDefinition(
            name="create_mock_hr_ticket",
            description="创建 HR 工单（需审批）",
            permission_scope="hr.ticket.write",
            risk_level=ToolRiskLevel.WRITE,
            requires_approval=True,
        ),
        MockTicketHandler(),
    )

    return registry


def _build_ai_adapters(settings: object) -> tuple[object, Embedder, Reranker]:
    """根据配置选择真实 Qwen adapter 或 deterministic fake。"""
    from app.services.retrieval.embedding.mock_embedding import MockEmbedder
    from app.services.retrieval.reranker.mock_reranker import MockReranker

    api_key = getattr(settings, "qwen_api_key", "")
    if not api_key:
        return (
            FakeAnswerGenerator(),
            MockEmbedder(dimension=getattr(settings, "embedding_dim", 1024)),
            MockReranker(),
        )

    from app.services.ai.qwen import QwenAnswerGenerator, QwenEmbedder, QwenReranker

    timeout_seconds = getattr(settings, "qwen_timeout_seconds", 30.0)
    return (
        QwenAnswerGenerator(
            api_key=api_key,
            model=getattr(settings, "qwen_chat_model", "qwen-plus"),
            base_url=getattr(
                settings,
                "qwen_api_base_url",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            timeout_seconds=timeout_seconds,
        ),
        QwenEmbedder(
            api_key=api_key,
            model=getattr(settings, "qwen_embedding_model", "text-embedding-v4"),
            dimension=getattr(settings, "embedding_dim", 1024),
            base_url=getattr(
                settings,
                "qwen_api_base_url",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            timeout_seconds=timeout_seconds,
        ),
        QwenReranker(
            api_key=api_key,
            model=getattr(settings, "qwen_rerank_model", "qwen3-rerank"),
            rerank_base_url=getattr(
                settings,
                "qwen_rerank_base_url",
                "https://dashscope.aliyuncs.com/compatible-api/v1",
            ),
            timeout_seconds=timeout_seconds,
        ),
    )


def _build_trace_exporter(settings: object) -> object:
    """根据运行模式选择 trace exporter。"""
    if getattr(settings, "app_mode", "fallback") == "full":
        from app.services.observability.exporters.otel_exporter import OTelTraceExporter

        return OTelTraceExporter(
            endpoint=getattr(settings, "phoenix_endpoint", "http://localhost:6006"),
            service_name="enterprisemind",
        )

    from app.services.observability.exporters.log_exporter import LogExporter

    return LogExporter()


def _build_tracer(settings: object) -> object:
    """构建统一 Tracer，fallback 输出日志，full 输出到 OTLP/Phoenix。"""
    from app.services.observability.tracer import Tracer

    return Tracer(exporter=_build_trace_exporter(settings))


# ── Service 容器 ─────────────────────────────────────────────────────

class ServiceContainer:
    """
    服务容器，持有全部 service 实例。

    路由层通过 Depends 注入具体 service。
    根据 app_mode 选择 in-memory 或真实外部服务。
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.tracer = _build_tracer(settings)

        # 基础组件（两种模式共用）
        self.step_logger = StepLogger()
        self.timeline_builder = ArtifactTimelineBuilder()
        self.approval_manager = ApprovalManager(step_logger=self.step_logger)
        self.tool_registry = _build_tool_registry()
        self.acl_validator = ACLValidator()
        self.tool_executor = ToolExecutor(
            registry=self.tool_registry,
            approval_manager=self.approval_manager,
            step_logger=self.step_logger,
            acl_validator=self.acl_validator,
        )

        # 根据模式选择服务实现
        if settings.app_mode == "full":
            self._init_full_mode(settings)
        else:
            self._init_fallback_mode()

    def _init_fallback_mode(self) -> None:
        """初始化 fallback 模式（全部 in-memory）。"""
        from app.services.ingestion.store import InMemoryIngestionTaskStore
        from app.services.retrieval.hybrid import HybridRetriever
        from app.services.retrieval.embedding.mock_embedding import MockEmbedder
        from app.services.retrieval.reranker.mock_reranker import MockReranker
        from app.services.retrieval.store.memory_bm25 import InMemoryBM25Store
        from app.services.retrieval.store.memory_vector import InMemoryVectorStore
        from app.services.storage.local_storage import LocalFileStorage

        self.answer_generator = FakeAnswerGenerator()
        self.embedder = MockEmbedder()
        self.reranker = MockReranker()
        self.vector_store = InMemoryVectorStore()
        self.bm25_store = InMemoryBM25Store()
        self.storage = LocalFileStorage(base_dir=self.settings.local_storage_dir)
        self.ingestion_task_store = InMemoryIngestionTaskStore()

        self.run_manager = AgentRunManager(
            tool_executor=self.tool_executor,
            approval_manager=self.approval_manager,
            step_logger=self.step_logger,
        )
        self.answer_service = GroundedAnswerService(
            answer_generator=self.answer_generator,
        )
        self.eval_runner = EvalRunner(
            answer_service=self.answer_service,
        )
        self.hybrid_retriever = HybridRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
            bm25_store=self.bm25_store,
            reranker=self.reranker,
        )
        self._init_graph_runner()

    def _init_full_mode(self, settings: object) -> None:
        """初始化 full 模式（接入真实外部服务）。"""
        from app.db.session import get_session_factory
        from app.services.retrieval.hybrid import HybridRetriever

        session_factory = get_session_factory()

        # 真实 MinIO 存储
        from app.services.storage.minio_storage import MinIOStorage
        self.storage = MinIOStorage(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
        )

        from app.services.ingestion.worker import build_task_store
        self.ingestion_task_store = build_task_store(settings)

        # 真实 Milvus 向量存储
        from app.services.retrieval.store.milvus_vector import MilvusVectorStore
        self.vector_store = MilvusVectorStore(
            host=settings.milvus_host,
            port=settings.milvus_port,
            dim=settings.embedding_dim,
        )

        # 真实 ES BM25 存储
        from app.services.retrieval.store.es_bm25 import ElasticsearchBM25Store
        self.bm25_store = ElasticsearchBM25Store(es_url=settings.es_url)

        # AI adapter：有 Qwen key 时使用真实模型，否则保持 deterministic fake。
        answer_generator, embedder, reranker = _build_ai_adapters(settings)
        self.answer_generator = answer_generator
        self.embedder = embedder
        self.reranker = reranker

        # 混合检索器
        self.hybrid_retriever = HybridRetriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
            bm25_store=self.bm25_store,
            reranker=self.reranker,
        )

        # Redis 速率限制器
        from app.services.security.redis_rate_limiter import RedisRateLimiter
        self.rate_limiter = RedisRateLimiter(redis_url=settings.redis_url)

        # Run Manager（带 PostgreSQL 持久化）
        self.run_manager = AgentRunManager(
            tool_executor=self.tool_executor,
            approval_manager=self.approval_manager,
            step_logger=self.step_logger,
            session_factory=session_factory,
        )

        self.answer_service = GroundedAnswerService(answer_generator=self.answer_generator)
        self.eval_runner = EvalRunner(
            answer_service=self.answer_service,
        )

        self._init_graph_runner()

    def _init_graph_runner(self) -> None:
        """构建 LangGraph Runner，供可选真实编排入口使用。"""
        from app.services.graph.graph import create_agent_graph
        from app.services.graph.runner import GraphRunner

        compiled_graph = create_agent_graph(
            run_manager=self.run_manager,
            hybrid_retriever=self.hybrid_retriever,
            answer_service=self.answer_service,
        )
        self.graph_runner = GraphRunner(
            graph=compiled_graph,
            run_manager=self.run_manager,
            step_logger=self.step_logger,
            tracer=self.tracer,
        )


_container: ServiceContainer | None = None


def get_container() -> ServiceContainer:
    """获取全局服务容器（单例）。"""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def reset_container() -> None:
    """重置容器（测试用）。"""
    global _container
    _container = None
