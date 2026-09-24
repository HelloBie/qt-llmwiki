import json
import time
import uuid
from typing import AsyncIterator, List, Optional
from app.core.config import Settings
from app.schemas.chat import ChatMessage, ChatResponse
from app.agents.runtime import AgentRuntime
from app.agents.messages import (
    schema_to_langchain_messages,
    langchain_messages_to_schema,
    extract_text_content,
)
from app.agents.llm import LLMNotConfiguredError


def format_sse(event: str, data: dict) -> str:
    """格式化标准 SSE 帧"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class ChatService:
    """对话应用编排服务"""

    def __init__(self, runtime: AgentRuntime, settings: Settings):
        self.runtime = runtime
        self.settings = settings

    async def chat(self, messages: List[ChatMessage], thread_id: Optional[str] = None) -> ChatResponse:
        """非流式对话"""
        if not thread_id:
            thread_id = uuid.uuid4().hex

        start_time = time.perf_counter()
        graph = await self.runtime.get_graph()

        lc_messages = schema_to_langchain_messages(messages)
        recursion_limit = 2 * self.settings.AGENT_MAX_ITERATIONS + 1

        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": recursion_limit,
        }

        try:
            result = await graph.ainvoke({"messages": lc_messages}, config=config)
        except Exception as e:
            raise RuntimeError(f"模型调用失败: {e}") from e

        history_msgs = result.get("messages", [])
        last_content = ""
        if history_msgs:
            last_content = extract_text_content(history_msgs[-1])

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        schema_msgs = langchain_messages_to_schema(history_msgs)

        return ChatResponse(
            thread_id=thread_id,
            content=last_content,
            messages=schema_msgs,
            elapsed_ms=elapsed_ms,
        )

    async def stream_chat(
        self, messages: List[ChatMessage], thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """SSE 流式对话"""
        if not thread_id:
            thread_id = uuid.uuid4().hex

        # 1. 发送 start 事件
        yield format_sse("start", {"thread_id": thread_id})

        try:
            graph = await self.runtime.get_graph()
        except LLMNotConfiguredError as e:
            yield format_sse("error", {"message": str(e)})
            return
        except Exception as e:
            yield format_sse("error", {"message": f"初始化智能体图失败: {e}"})
            return

        lc_messages = schema_to_langchain_messages(messages)
        recursion_limit = 2 * self.settings.AGENT_MAX_ITERATIONS + 1
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": recursion_limit,
        }

        try:
            # 监听 LangGraph 统一事件流
            async for event in graph.astream_events(
                {"messages": lc_messages}, config=config, version="v2"
            ):
                event_type = event.get("event")
                metadata = event.get("metadata", {})
                node = metadata.get("langgraph_node", "agent")

                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    text = extract_text_content(chunk)
                    if text:
                        yield format_sse("token", {"node": node, "text": text})

                elif event_type == "on_tool_start":
                    name = event.get("name", "tool")
                    args = event.get("data", {}).get("input", {})
                    yield format_sse("tool_call", {"node": node, "name": name, "args": args})

                elif event_type == "on_tool_end":
                    name = event.get("name", "tool")
                    output = event.get("data", {}).get("output", "")
                    content_str = extract_text_content(output)
                    yield format_sse("tool_result", {"node": node, "name": name, "content": content_str})

            # 2. 正常完成
            yield format_sse("done", {"thread_id": thread_id})

        except Exception as e:
            yield format_sse("error", {"message": f"流式处理中异常: {str(e)}"})
