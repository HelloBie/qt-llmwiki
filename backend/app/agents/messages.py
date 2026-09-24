from typing import List, Any
from app.schemas.chat import ChatMessage

try:
    from langchain_core.messages import (
        BaseMessage,
        SystemMessage,
        HumanMessage,
        AIMessage,
        ToolMessage,
    )
except ImportError:
    # 兼容基础备选对象
    class BaseMessage:  # type: ignore
        def __init__(self, content: str):
            self.content = content

    class SystemMessage(BaseMessage):
        pass

    class HumanMessage(BaseMessage):
        pass

    class AIMessage(BaseMessage):
        pass

    class ToolMessage(BaseMessage):
        def __init__(self, content: str, tool_call_id: str = "call_mock"):
            super().__init__(content)
            self.tool_call_id = tool_call_id


def extract_text_content(msg: Any) -> str:
    """安全提取消息中的文本内容，兼容不同版本的 langchain-core 及其嵌套结构"""
    if msg is None:
        return ""
    if isinstance(msg, str):
        return msg

    # 尝试 message.text (某些版本为属性或方法)
    if hasattr(msg, "text"):
        attr = getattr(msg, "text")
        if callable(attr):
            try:
                res = attr()
                if isinstance(res, str) and res:
                    return res
            except Exception:
                pass
        elif isinstance(attr, str) and attr:
            return attr

    # 提取 content
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # 可能是多模态或 content block 列表: [{'type': 'text', 'text': '...'}]
        chunks = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
            elif isinstance(part, dict) and "text" in part:
                chunks.append(str(part["text"]))
            else:
                chunks.append(str(part))
        return "".join(chunks)
    return str(content)


def schema_to_langchain_messages(messages: List[ChatMessage], system_prompt: str = "") -> List[Any]:
    """将业务层 ChatMessage 转换为 LangChain BaseMessage 列表"""
    lc_messages = []
    if system_prompt:
        lc_messages.append(SystemMessage(content=system_prompt))

    for m in messages:
        role = m.role.lower()
        if role == "system":
            lc_messages.append(SystemMessage(content=m.content))
        elif role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=m.content))
        elif role == "tool":
            lc_messages.append(ToolMessage(content=m.content, tool_call_id="call_legacy"))
        else:
            lc_messages.append(HumanMessage(content=m.content))
    return lc_messages


def langchain_messages_to_schema(lc_messages: List[Any]) -> List[ChatMessage]:
    """将 LangChain 消息列表转换为前端和响应所需的 ChatMessage 列表"""
    result = []
    for msg in lc_messages:
        text = extract_text_content(msg)
        if isinstance(msg, SystemMessage):
            role = "system"
        elif isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, ToolMessage):
            role = "tool"
        else:
            msg_type = getattr(msg, "type", "")
            if msg_type in ("human", "user"):
                role = "user"
            elif msg_type in ("ai", "assistant"):
                role = "assistant"
            elif msg_type == "system":
                role = "system"
            elif msg_type == "tool":
                role = "tool"
            else:
                role = "assistant"
        result.append(ChatMessage(role=role, content=text))
    return result
