import pytest
from typing import List, Any, AsyncIterator
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.agents.runtime import AgentRuntime
from app.agents.messages import AIMessage, extract_text_content
from app.main import create_app


class EchoChatModel:
    """测试用假模型：返回最后一条消息的 Echo 回复，无需联网与 API Key"""

    def __init__(self, prefix: str = "Echo: "):
        self.prefix = prefix

    def invoke(self, messages: List[Any], **kwargs) -> AIMessage:
        last = messages[-1] if messages else ""
        text = extract_text_content(last)
        return AIMessage(content=f"{self.prefix}{text}")

    async def ainvoke(self, messages: List[Any], **kwargs) -> AIMessage:
        return self.invoke(messages, **kwargs)

    async def astream(self, messages: List[Any], **kwargs) -> AsyncIterator[AIMessage]:
        full = self.invoke(messages, **kwargs).content
        for word in full.split(" "):
            yield AIMessage(content=word + " ")


@pytest.fixture
def mock_settings() -> Settings:
    """包含假 Key 的测试设置"""
    return Settings(
        APP_NAME="qtllmwiki-test",
        APP_ENV="test",
        LLM_API_KEY="sk-mock-key-for-test",
        LLM_MODEL="mock-model",
    )


@pytest.fixture
def unconfigured_settings() -> Settings:
    """未配置 Key 的测试设置"""
    return Settings(
        APP_NAME="qtllmwiki-test",
        APP_ENV="test",
        LLM_API_KEY=None,
    )


@pytest.fixture
def mock_runtime(mock_settings: Settings) -> AgentRuntime:
    """注入假模型的 AgentRuntime"""
    return AgentRuntime(
        settings=mock_settings,
        custom_llm=EchoChatModel(),
        custom_tools=[],
    )


@pytest.fixture
def client(mock_settings: Settings, mock_runtime: AgentRuntime) -> TestClient:
    """就绪态测试客户端"""
    app = create_app(custom_settings=mock_settings, custom_runtime=mock_runtime)
    return TestClient(app)


@pytest.fixture
def unconfigured_client(unconfigured_settings: Settings) -> TestClient:
    """未配置 Key 的测试客户端"""
    runtime = AgentRuntime(settings=unconfigured_settings)
    app = create_app(custom_settings=unconfigured_settings, custom_runtime=runtime)
    return TestClient(app)
