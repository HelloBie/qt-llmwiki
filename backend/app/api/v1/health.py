from fastapi import APIRouter
from app.api.deps import SettingsDep, RuntimeDep
from app.schemas.chat import HealthResponse, ReadyResponse
from app.agents.tools import DEFAULT_TOOLS

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="服务健康状态检查")
async def check_health(settings: SettingsDep) -> HealthResponse:
    """存活探针：未配置 API Key 时返回 degraded，正常配置返回 healthy"""
    is_configured = settings.is_llm_configured
    status = "healthy" if is_configured else "degraded"

    return HealthResponse(
        status=status,
        app=settings.APP_NAME,
        env=settings.APP_ENV,
        llm_configured=is_configured,
        llm_model=settings.LLM_MODEL,
        tools_count=len(DEFAULT_TOOLS),
    )


@router.get("/health/ready", response_model=ReadyResponse, summary="服务就绪探针")
async def check_ready(runtime: RuntimeDep) -> ReadyResponse:
    """就绪探针：尝试预热图构建以确认组件就绪"""
    ready = await runtime.is_ready()
    message = "Agent 运行时准备就绪" if ready else "Agent 运行时未就绪或未配置 API Key"
    return ReadyResponse(ready=ready, message=message)
