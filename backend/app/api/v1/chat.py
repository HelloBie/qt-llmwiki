from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import SettingsDep, RuntimeDep
from app.schemas.chat import ChatRequest, ChatResponse, ToolInfo
from app.services.chat_service import ChatService
from app.agents.tools import get_tools_info
from app.agents.llm import LLMNotConfiguredError

router = APIRouter(tags=["chat"])


@router.get("/chat/tools", response_model=List[ToolInfo], summary="获取智能体注册工具列表")
async def list_tools() -> List[ToolInfo]:
    """返回 Agent 当前注册的工具元数据"""
    return get_tools_info()


@router.post("/chat", response_model=ChatResponse, summary="一轮同步对话")
async def sync_chat(
    req: ChatRequest,
    runtime: RuntimeDep,
    settings: SettingsDep,
) -> ChatResponse:
    """非流式对话接口"""
    if not runtime.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="大模型未配置有效 API Key，请在 backend/.env 中配置 LLM_API_KEY",
        )

    service = ChatService(runtime=runtime, settings=settings)
    try:
        return await service.chat(messages=req.messages, thread_id=req.thread_id)
    except LLMNotConfiguredError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"上游模型调用失败: {e}")


@router.post("/chat/stream", summary="SSE 流式对话")
async def stream_chat(
    req: ChatRequest,
    runtime: RuntimeDep,
    settings: SettingsDep,
):
    """SSE 流式对话接口"""
    if not runtime.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="大模型未配置有效 API Key，请在 backend/.env 中配置 LLM_API_KEY",
        )

    service = ChatService(runtime=runtime, settings=settings)
    generator = service.stream_chat(messages=req.messages, thread_id=req.thread_id)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
