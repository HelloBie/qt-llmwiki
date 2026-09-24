from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """对话消息项"""
    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., description="消息角色: system / user / assistant / tool"
    )
    content: str = Field(..., description="消息文本内容")


class ChatRequest(BaseModel):
    """对话请求"""
    messages: List[ChatMessage] = Field(..., min_length=1, description="会话上下文消息列表，至少一条")
    thread_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="可选会话 ID，用于多轮对话记忆隔离；不传时由服务端自动生成"
    )

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: List[ChatMessage]) -> List[ChatMessage]:
        if not v:
            raise ValueError("messages 列表不能为空")
        return v


class ChatResponse(BaseModel):
    """非流式对话响应"""
    thread_id: str = Field(..., description="当前会话 ID")
    content: str = Field(..., description="AI 本轮最终回复正文")
    messages: List[ChatMessage] = Field(..., description="当前完整会话消息历史")
    elapsed_ms: float = Field(..., description="总处理耗时(毫秒)")


class ToolParameterProperty(BaseModel):
    type: str
    description: Optional[str] = None


class ToolInfo(BaseModel):
    """注册工具元数据"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具用途描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数 JSON Schema")


class HealthResponse(BaseModel):
    """服务健康检查响应"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="健康状态")
    app: str = Field(..., description="应用服务名")
    env: str = Field(..., description="当前运行环境")
    llm_configured: bool = Field(..., description="是否已配置 LLM API Key")
    llm_model: str = Field(..., description="当前配置的模型")
    tools_count: int = Field(..., description="已注册工具数")


class ReadyResponse(BaseModel):
    """服务就绪检查响应"""
    ready: bool = Field(..., description="Agent 运行时是否就绪")
    message: str = Field(..., description="就绪说明或错误原因")
