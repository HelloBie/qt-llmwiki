import datetime
from typing import List, Dict, Any, Callable
from app.schemas.chat import ToolInfo


def get_current_time() -> str:
    """获取系统当前准确的日期和时间。"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


def search_knowledge_base(query: str) -> str:
    """在知识库中检索与问题相关的事实、文档片段和参考资料。

    Args:
        query: 检索关键词或自然语言问题
    """
    # 占位实现：便于后续替换对接真实的向量数据库（如 Chroma / Milvus / FAISS）或全文检索
    return (
        f"【知识库检索结果占位】已收到针对检索词 '{query}' 的查询请求。"
        "当前系统处于脚手架阶段，知识库尚未填充真实企业数据。"
        "后续可在 backend/app/agents/tools.py 中对接向量数据库以支持真实检索。"
    )


# 尝试使用 LangChain @tool 装饰器封装
try:
    from langchain_core.tools import tool

    tool_get_current_time = tool(get_current_time)
    tool_search_knowledge_base = tool(search_knowledge_base)
    DEFAULT_TOOLS = [tool_get_current_time, tool_search_knowledge_base]
except Exception:
    # 降级备用工具包装对象
    class SimpleTool:
        def __init__(self, func: Callable, name: str, description: str):
            self.func = func
            self.name = name
            self.description = description

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

        def invoke(self, args: Dict[str, Any]) -> str:
            if isinstance(args, dict):
                return str(self.func(**args))
            return str(self.func(args))

    tool_get_current_time = SimpleTool(
        get_current_time,
        name="get_current_time",
        description="获取系统当前准确的日期和时间。"
    )
    tool_search_knowledge_base = SimpleTool(
        search_knowledge_base,
        name="search_knowledge_base",
        description="在知识库中检索与问题相关的事实、文档片段和参考资料。"
    )
    DEFAULT_TOOLS = [tool_get_current_time, tool_search_knowledge_base]


def get_tools_info() -> List[ToolInfo]:
    """返回供前端和接口查询的已注册工具元数据列表"""
    tools_info = []
    for t in DEFAULT_TOOLS:
        name = getattr(t, "name", getattr(t, "__name__", "unknown"))
        description = getattr(t, "description", getattr(t, "__doc__", "") or "")
        description = description.strip()
        # 提取参数 schema
        args_schema = {}
        if hasattr(t, "args_schema") and t.args_schema:
            try:
                args_schema = t.args_schema.model_json_schema()
            except Exception:
                args_schema = {"type": "object"}
        elif hasattr(t, "args"):
            args_schema = {"properties": getattr(t, "args", {})}
        elif name == "search_knowledge_base":
            args_schema = {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "检索关键词"}},
                "required": ["query"],
            }
        else:
            args_schema = {"type": "object", "properties": {}}

        tools_info.append(
            ToolInfo(
                name=name,
                description=description,
                parameters=args_schema,
            )
        )
    return tools_info
