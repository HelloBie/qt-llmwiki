import asyncio
from typing import Any, Optional, List
from app.core.config import Settings
from app.agents.tools import DEFAULT_TOOLS
from app.agents.llm import create_chat_model, LLMNotConfiguredError
from app.agents.graph import build_agent_graph


class AgentRuntime:
    """Agent 运行时管理器，负责惰性初始化与缓存编译后的 LangGraph 图。"""

    def __init__(self, settings: Settings, custom_llm: Any = None, custom_tools: Optional[List[Any]] = None):
        self.settings = settings
        self.custom_llm = custom_llm
        self.custom_tools = custom_tools
        self._graph: Optional[Any] = None
        self._lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        """检查基础 LLM 凭据是否具备"""
        if self.custom_llm is not None:
            return True
        return self.settings.is_llm_configured

    async def get_graph(self) -> Any:
        """异步获取已编译的图，使用加锁双检保证线程/协程安全惰性初始化"""
        if self._graph is not None:
            return self._graph

        async with self._lock:
            if self._graph is not None:
                return self._graph

            # 检查是否有凭据
            if not self.is_configured:
                raise LLMNotConfiguredError(
                    "服务尚未配置有效的大模型 API Key (LLM_API_KEY)，请在前端「模型设置」或 config.yaml 中配置。"
                )

            # 构建 LLM 和图
            llm = self.custom_llm if self.custom_llm is not None else create_chat_model(self.settings)
            tools = self.custom_tools if self.custom_tools is not None else DEFAULT_TOOLS

            self._graph = build_agent_graph(
                llm=llm,
                tools=tools,
                system_prompt=self.settings.SYSTEM_PROMPT,
            )
            return self._graph

    async def is_ready(self) -> bool:
        """就绪探针，尝试验证图能否被正常构建"""
        try:
            await self.get_graph()
            return True
        except Exception:
            return False

    def reset(self) -> None:
        """清除已缓存的图，用于热重载或重新初始化"""
        self._graph = None
