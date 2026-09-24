import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import httpx

from app.api.deps import SettingsDep, RuntimeDep
from app.core.yaml_config import load_yaml_config, save_yaml_config, sync_yaml_to_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class OpenAIModelConfig(BaseModel):
    base_url: str = Field(default="https://api.openai.com/v1", description="API 基础端点")
    api_key: str = Field(default="", description="API 密钥")
    model: str = Field(default="gpt-4o", description="模型名称")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="采样温度")
    max_tokens: int = Field(default=4096, ge=1, le=128000, description="最大输出 Token 数")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="核采样")
    organization: Optional[str] = Field(default="", description="组织 ID")
    project_id: Optional[str] = Field(default="", description="项目 ID")


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
    """读取 config.yaml，并返回当前的 OpenAI 协议配置"""
    raw_cfg = load_yaml_config()
    openai_cfg = raw_cfg.get("openai", {})
    return OpenAIModelConfig(
        base_url=openai_cfg.get("base_url", "https://api.openai.com/v1"),
        api_key=openai_cfg.get("api_key", ""),
        model=openai_cfg.get("model", "gpt-4o"),
        temperature=float(openai_cfg.get("temperature", 0.7)),
        max_tokens=int(openai_cfg.get("max_tokens", 4096)),
        top_p=float(openai_cfg.get("top_p", 1.0)),
        organization=openai_cfg.get("organization", ""),
        project_id=openai_cfg.get("project_id", ""),
    )


@router.post("/config", summary="保存模型配置到 config.yaml")
async def save_model_config(
    new_cfg: OpenAIModelConfig,
    settings: SettingsDep,
    runtime: RuntimeDep,
):
    """将前端设置写入 config.yaml，并热更新内存配置与智能体运行时"""
    raw_cfg = load_yaml_config()
    raw_cfg["openai"] = new_cfg.model_dump()

    # 写入 config.yaml
    save_yaml_config(raw_cfg)

    # 同步到 Settings 单例
    sync_yaml_to_settings(settings)

    # 重置 Agent 图缓存，确保下次会话立即使用新配置与新模型
    runtime.reset()

    return {
        "success": True,
        "message": "配置已成功保存并写入 config.yaml，当前会话已生效",
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
