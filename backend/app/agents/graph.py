import asyncio
from typing import Any, List, Optional, Dict, AsyncIterator
from app.agents.messages import extract_text_content, AIMessage, HumanMessage

try:
    from langgraph.prebuilt import create_react_agent
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    MemorySaver = None  # type: ignore


class FallbackAgentGraph:
    """当未安装 langgraph 时提供的兼容 Agent 运行时执行器。
    提供一致的 ainvoke 与 astream_events 接口，保障服务在任何情况下不崩溃。
    """
    def __init__(self, llm: Any, tools: List[Any], checkpointer: Any = None):
        self.llm = llm
        self.tools = tools
        self.checkpointer = checkpointer
        self.memory: Dict[str, List[Any]] = {}

    async def ainvoke(self, inputs: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config = config or {}
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        incoming_msgs = inputs.get("messages", [])

        history = self.memory.setdefault(thread_id, [])
        history.extend(incoming_msgs)

        if hasattr(self.llm, "ainvoke"):
            response = await self.llm.ainvoke(history)
        elif hasattr(self.llm, "invoke"):
            response = self.llm.invoke(history)
        else:
            response = AIMessage(content="[Local Agent] 消息已接收。")

        history.append(response)
        return {"messages": history}

    async def astream_events(
        self, inputs: Dict[str, Any], config: Optional[Dict[str, Any]] = None, version: str = "v2"
    ) -> AsyncIterator[Dict[str, Any]]:
        config = config or {}
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        incoming_msgs = inputs.get("messages", [])
        history = self.memory.setdefault(thread_id, [])
        history.extend(incoming_msgs)

        if hasattr(self.llm, "astream"):
            full_content = []
            async for chunk in self.llm.astream(history):
                text = extract_text_content(chunk)
                if text:
                    full_content.append(text)
                    yield {
                        "event": "on_chat_model_stream",
                        "metadata": {"langgraph_node": "agent"},
                        "data": {"chunk": chunk},
                    }
            history.append(AIMessage(content="".join(full_content)))
        else:
            # 单步执行并切分返回
            res = await self.ainvoke(inputs, config)
            last_msg = res["messages"][-1]
            text = extract_text_content(last_msg)
            # 模拟流式下发
            for char in text:
                yield {
                    "event": "on_chat_model_stream",
                    "metadata": {"langgraph_node": "agent"},
                    "data": {"chunk": AIMessage(content=char)},
                }
                await asyncio.sleep(0.01)


def build_agent_graph(
    llm: Any,
    tools: List[Any],
    checkpointer: Any = None,
    system_prompt: str = "",
) -> Any:
    """构建 LangGraph 智能体状态图"""
    if LANGGRAPH_AVAILABLE:
        if checkpointer is None and MemorySaver is not None:
            checkpointer = MemorySaver()

        # 使用 LangGraph 内置的 create_react_agent
        graph = create_react_agent(
            model=llm,
            tools=tools,
            checkpointer=checkpointer,
            prompt=system_prompt if system_prompt else None,
        )
        return graph
    else:
        return FallbackAgentGraph(llm=llm, tools=tools, checkpointer=checkpointer)
