import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import httpx

from app.api.deps import SettingsDep, RuntimeDep
from app.core.yaml_config import load_yaml_config, save_yaml_config, sync_yaml_to_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class ModelRoleConfig(BaseModel):
    name: str = Field(default="", description="模型标识 (例如 deepseek-chat, bge-m3 等)")
    base_url: Optional[str] = Field(default="", description="独立 API 基础端点 (为空则继承全局 Base URL)")
    api_key: Optional[str] = Field(default="", description="独立 API 密钥 (为空则继承全局 Key)")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="采样温度 (生成类模型)")
    max_tokens: Optional[int] = Field(default=4096, ge=128, le=128000, description="最大生成 Token")
    top_n: Optional[int] = Field(default=5, ge=1, le=50, description="截取数量 (重排模型)")
    dimension: Optional[int] = Field(default=1024, ge=64, le=8192, description="向量维度 (向量模型)")
    description: Optional[str] = Field(default="", description="用途职责描述")


class OpenAIModelConfig(BaseModel):
    base_url: str = Field(default="https://api.openai.com/v1", description="API 基础端点")
    api_key: str = Field(default="", description="API 密钥")
    model: str = Field(default="gpt-4o", description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="采样温度")
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="最大输出 Token 数")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="核采样")
    organization: Optional[str] = Field(default="", description="组织 ID")
    project_id: Optional[str] = Field(default="", description="项目 ID")

    # 五大分工模型角色独立配置
    chat: Optional[ModelRoleConfig] = Field(default=None, description="对话主模型")
    digest: Optional[ModelRoleConfig] = Field(default=None, description="文件消化解析模型")
    embedding: Optional[ModelRoleConfig] = Field(default=None, description="向量编码模型")
    rerank: Optional[ModelRoleConfig] = Field(default=None, description="语义重排模型")
    expansion: Optional[ModelRoleConfig] = Field(default=None, description="查询扩展模型")


class TestConnectionRequest(BaseModel):
    base_url: str
    api_key: str
    model: Optional[str] = None


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    latency_ms: float
    status_code: Optional[int] = None
    available_models_count: Optional[int] = None
    models: List[str] = Field(default_factory=list, description="获取到的可用模型ID列表")


def extract_model_ids(data: Any) -> List[str]:
    """从上游返回的数据结构中智能解析提取模型标识列表"""
    raw_items: List[Any] = []
    if isinstance(data, dict):
        raw_items = data.get("data") or data.get("models") or []
    elif isinstance(data, list):
        raw_items = data

    models: List[str] = []
    if isinstance(raw_items, list):
        for item in raw_items:
            if isinstance(item, dict):
                m_id = item.get("id") or item.get("name") or item.get("model")
                if m_id and isinstance(m_id, str):
                    models.append(m_id.strip())
            elif isinstance(item, str):
                models.append(item.strip())

    # 去重并保持顺序
    seen = set()
    return [m for m in models if m and not (m in seen or seen.add(m))]


@router.get("/config", response_model=OpenAIModelConfig, summary="读取当前 config.yaml 中的模型配置")
async def get_model_config() -> OpenAIModelConfig:
    """读取 config.yaml，并返回当前的全局与多角色模型配置"""
    raw_cfg = load_yaml_config()
    openai_cfg = raw_cfg.get("openai", {})
    models_cfg = raw_cfg.get("models", {})

    def get_role_cfg(role_key: str, default_name: str, **default_extras) -> ModelRoleConfig:
        rc = models_cfg.get(role_key, {})
        return ModelRoleConfig(
            name=rc.get("name", default_name),
            base_url=rc.get("base_url", default_extras.get("base_url", "")),
            api_key=rc.get("api_key", default_extras.get("api_key", "")),
            temperature=rc.get("temperature", default_extras.get("temperature", 0.7)),
            max_tokens=rc.get("max_tokens", default_extras.get("max_tokens", 4096)),
            top_n=rc.get("top_n", default_extras.get("top_n", 5)),
            dimension=rc.get("dimension", default_extras.get("dimension", 1024)),
            description=rc.get("description", default_extras.get("description", "")),
        )

    base_model = openai_cfg.get("model", "deepseek-chat")
    chat_cfg = get_role_cfg(
        "chat",
        base_model,
        temperature=float(openai_cfg.get("temperature", 0.7)),
        description="主问答对话模型，面向用户交互，负责综合推理与高质量解答",
    )
    digest_cfg = get_role_cfg(
        "digest",
        "qwen-plus",
        temperature=0.3,
        description="文件消化解析模型，负责文档解析、知识库构建与实体结构化提炼",
    )
    embedding_cfg = get_role_cfg(
        "embedding",
        "bge-m3",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        dimension=1024,
        description="向量嵌入模型，负责知识库文档切片语义编码与相似度检索",
    )
    rerank_cfg = get_role_cfg(
        "rerank",
        "bge-reranker-v2-m3",
        base_url="http://localhost:11434",
        api_key="ollama",
        top_n=5,
        description="语义重排模型，负责候选文本块 Cross-Encoder 精准打分与过滤",
    )
    expansion_cfg = get_role_cfg(
        "expansion",
        "qwen2.5:1.5b",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        temperature=0.3,
        description="查询扩展模型，负责用户提问多角度改写与关键词提取",
    )

    return OpenAIModelConfig(
        base_url=openai_cfg.get("base_url", "https://api.openai.com/v1"),
        api_key=openai_cfg.get("api_key", ""),
        model=chat_cfg.name or base_model,
        temperature=float(openai_cfg.get("temperature", 0.7)),
        max_tokens=int(openai_cfg.get("max_tokens", 4096)),
        top_p=float(openai_cfg.get("top_p", 1.0)),
        organization=openai_cfg.get("organization", ""),
        project_id=openai_cfg.get("project_id", ""),
        chat=chat_cfg,
        digest=digest_cfg,
        embedding=embedding_cfg,
        rerank=rerank_cfg,
        expansion=expansion_cfg,
    )


@router.post("/config", summary="保存模型配置到 config.yaml")
async def save_model_config(
    new_cfg: OpenAIModelConfig,
    settings: SettingsDep,
    runtime: RuntimeDep,
):
    """将前端设置写入 config.yaml，并热更新内存配置与智能体运行时"""
    raw_cfg = load_yaml_config()

    # 1. 保存全局 openai 基础兼容配置
    openai_data = {
        "base_url": new_cfg.base_url,
        "api_key": new_cfg.api_key,
        "model": new_cfg.chat.name if new_cfg.chat and new_cfg.chat.name else new_cfg.model,
        "temperature": new_cfg.chat.temperature if new_cfg.chat and new_cfg.chat.temperature is not None else new_cfg.temperature,
        "max_tokens": new_cfg.chat.max_tokens if new_cfg.chat and new_cfg.chat.max_tokens is not None else new_cfg.max_tokens,
        "top_p": new_cfg.top_p,
        "organization": new_cfg.organization or "",
        "project_id": new_cfg.project_id or "",
    }
    raw_cfg["openai"] = openai_data

    # 2. 保存五大角色模型的独立配置
    models_data = raw_cfg.get("models", {})
    if new_cfg.chat is not None:
        models_data["chat"] = new_cfg.chat.model_dump()
    if new_cfg.digest is not None:
        models_data["digest"] = new_cfg.digest.model_dump()
    if new_cfg.embedding is not None:
        models_data["embedding"] = new_cfg.embedding.model_dump()
    if new_cfg.rerank is not None:
        models_data["rerank"] = new_cfg.rerank.model_dump()
    if new_cfg.expansion is not None:
        models_data["expansion"] = new_cfg.expansion.model_dump()

    raw_cfg["models"] = models_data

    # 写入 config.yaml
    save_yaml_config(raw_cfg)

    # 同步到 Settings 单例
    sync_yaml_to_settings(settings)

    # 重置 Agent 图缓存，确保下次会话立即使用新配置与新模型
    runtime.reset()

    return {
        "success": True,
        "message": "模型配置已成功保存并写入 config.yaml，当前会话已实时生效",
        "saved_config": new_cfg,
    }


@router.post("/test-connection", response_model=TestConnectionResponse, summary="真实测试与大模型端点的网络连通性")
async def test_endpoint_connection(req: TestConnectionRequest) -> TestConnectionResponse:
    """通过向 {base_url}/models 发送轻量请求来校验端点与密钥是否通畅，并返回所有可用模型列表"""
    base_url = req.base_url.rstrip("/")
    api_key = req.api_key.strip()

    target_url = f"{base_url}/models"
    headers = {
        "User-Agent": "qtllmwiki-client/0.1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(target_url, headers=headers)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    model_ids = extract_model_ids(data)
                except Exception:
                    model_ids = []
                models_count = len(model_ids)
                return TestConnectionResponse(
                    success=True,
                    message=f"连通成功！端点正常，获取到 {models_count} 个可用模型",
                    latency_ms=elapsed_ms,
                    status_code=resp.status_code,
                    available_models_count=models_count,
                    models=model_ids,
                )
            elif resp.status_code == 404 and not base_url.endswith("/v1"):
                # 若未带 /v1 且 404，尝试请求 /v1/models
                alt_url = f"{base_url}/v1/models"
                alt_resp = await client.get(alt_url, headers=headers)
                alt_elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
                if alt_resp.status_code == 200:
                    try:
                        data = alt_resp.json()
                        model_ids = extract_model_ids(data)
                    except Exception:
                        model_ids = []
                    models_count = len(model_ids)
                    return TestConnectionResponse(
                        success=True,
                        message=f"连通成功！检测到 {models_count} 个可用模型 (通过 /v1/models)",
                        latency_ms=alt_elapsed_ms,
                        status_code=alt_resp.status_code,
                        available_models_count=models_count,
                        models=model_ids,
                    )
                return TestConnectionResponse(
                    success=True,
                    message="端点网络连通 (HTTP 404，未开放 /models 索引，基础网络正常)",
                    latency_ms=elapsed_ms,
                    status_code=resp.status_code,
                    models=[],
                )
            elif resp.status_code == 401:
                return TestConnectionResponse(
                    success=False,
                    message="连通失败：API Key 无效或未授权 (HTTP 401 Unauthorized)",
                    latency_ms=elapsed_ms,
                    status_code=resp.status_code,
                    models=[],
                )
            elif resp.status_code == 404:
                return TestConnectionResponse(
                    success=True,
                    message="端点网络连通 (HTTP 404，未开放 /models 索引，基础网络正常)",
                    latency_ms=elapsed_ms,
                    status_code=resp.status_code,
                    models=[],
                )
            else:
                return TestConnectionResponse(
                    success=False,
                    message=f"端点返回状态码: HTTP {resp.status_code} ({resp.text[:120]})",
                    latency_ms=elapsed_ms,
                    status_code=resp.status_code,
                    models=[],
                )
    except httpx.ConnectError as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
        return TestConnectionResponse(
            success=False,
            message=f"无法连接到目标主机，请检查 Base URL 地址: {e}",
            latency_ms=elapsed_ms,
            models=[],
        )
    except httpx.TimeoutException:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
        return TestConnectionResponse(
            success=False,
            message="请求连接超时 (10秒未响应)，请检查网络或代理",
            latency_ms=elapsed_ms,
            models=[],
        )
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)
        return TestConnectionResponse(
            success=False,
            message=f"请求发生异常: {str(e)}",
            latency_ms=elapsed_ms,
            models=[],
        )


@router.post("/models", response_model=TestConnectionResponse, summary="从目标端点获取可用模型列表")
async def get_remote_models(req: TestConnectionRequest) -> TestConnectionResponse:
    """拉取目标 OpenAI 兼容端点所提供的全部模型 ID 列表"""
    return await test_endpoint_connection(req)


# ==============================================================================
# 系统工程设计文档 (HLD / DD / DBD / API / README)
# ==============================================================================

class DocMeta(BaseModel):
    id: str = Field(..., description="文档标识")
    filename: str = Field(..., description="文档文件名")
    title: str = Field(..., description="文档标题")
    badge: str = Field(..., description="文档分类徽章")
    description: str = Field(..., description="文档简要描述")
    size_bytes: int = Field(default=0, description="文件大小（字节）")
    line_count: int = Field(default=0, description="行数")
    updated_at: str = Field(default="", description="最后更新时间")


class DocDetail(DocMeta):
    content: str = Field(..., description="Markdown 原始正文文本")


DOCS_REGISTRY: List[Dict[str, str]] = [
    {
        "id": "01_hld",
        "filename": "01_概要设计说明书_总体设计.md",
        "title": "01 概要设计说明书（总体设计）",
        "badge": "HLD",
        "description": "系统总体架构、技术栈、部署拓扑、数据流与模块依赖设计",
    },
    {
        "id": "02_dd",
        "filename": "02_详细设计说明书_DD.md",
        "title": "02 详细设计说明书（DD）",
        "badge": "DD",
        "description": "模块内部逻辑、核心服务、LangGraph 智能体状态机与算法时序",
    },
    {
        "id": "03_dbd",
        "filename": "03_数据库设计文档_DBD.md",
        "title": "03 数据库设计文档（DBD）",
        "badge": "DBD",
        "description": "实体关系 ER 图、SQLite 数据库表结构、字段索引与持久化策略",
    },
    {
        "id": "04_api",
        "filename": "04_接口设计文档_API.md",
        "title": "04 接口设计文档（API Doc）",
        "badge": "API",
        "description": "前后端 RESTful / SSE 流式接口、参数契约、错误码与鉴权方式",
    },
    {
        "id": "readme",
        "filename": "README.md",
        "title": "系统工程设计文档索引",
        "badge": "INDEX",
        "description": "工程技术架构标准与设计规约索引目录",
    },
]


def get_docs_dir() -> Path:
    """按优先级探测系统设计文档目录所在位置"""
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent.parent / "docs",
        Path("/app/docs"),
        Path("docs").resolve(),
        Path("../docs").resolve(),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


@router.get("/docs", response_model=List[DocMeta], summary="获取系统工程设计文档列表")
async def list_design_docs() -> List[DocMeta]:
    """读取 docs/ 目录下所有标准化工程设计文档的元数据信息"""
    docs_dir = get_docs_dir()
    results: List[DocMeta] = []

    for item in DOCS_REGISTRY:
        file_path = docs_dir / item["filename"]
        size_bytes = 0
        line_count = 0
        updated_at = ""

        if file_path.exists() and file_path.is_file():
            stat = file_path.stat()
            size_bytes = stat.st_size
            updated_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            try:
                content = file_path.read_text(encoding="utf-8")
                line_count = len(content.splitlines())
            except Exception:
                pass

        results.append(
            DocMeta(
                id=item["id"],
                filename=item["filename"],
                title=item["title"],
                badge=item["badge"],
                description=item["description"],
                size_bytes=size_bytes,
                line_count=line_count,
                updated_at=updated_at,
            )
        )
    return results


@router.get("/docs/{doc_id}", response_model=DocDetail, summary="获取指定设计文档的完整 Markdown 内容")
async def get_design_doc_detail(doc_id: str) -> DocDetail:
    """获取指定设计文档的详情与完整 Markdown 正文（安全白名单匹配防路径穿越）"""
    docs_dir = get_docs_dir()

    target = None
    for item in DOCS_REGISTRY:
        if item["id"] == doc_id or item["filename"] == doc_id:
            target = item
            break

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到指定的设计文档: {doc_id}",
        )

    file_path = docs_dir / target["filename"]
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设计文档文件在服务端不存在: {target['filename']}",
        )

    try:
        content = file_path.read_text(encoding="utf-8")
        stat = file_path.stat()
        return DocDetail(
            id=target["id"],
            filename=target["filename"],
            title=target["title"],
            badge=target["badge"],
            description=target["description"],
            size_bytes=stat.st_size,
            line_count=len(content.splitlines()),
            updated_at=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            content=content,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取文档内容失败: {str(e)}",
        )

