import os
from typing import Any, Optional
from app.core.config import Settings


class LLMNotConfiguredError(RuntimeError):
    """未配置 LLM_API_KEY 时触发的异常"""
    pass


class LLMInvocationError(RuntimeError):
    """调用上游 LLM 接口失败时触发的异常"""
    pass


def get_api_key(settings: Settings) -> Optional[str]:
    """获取 API Key，优先 settings，其次系统环境变量"""
    key = settings.LLM_API_KEY or os.environ.get("OPENAI_API_KEY")
    if key and key.strip():
        return key.strip()
    return None


def create_chat_model(settings: Settings) -> Any:
    """根据 settings 构建 LangChain ChatModel 实例"""
    api_key = get_api_key(settings)
    if not api_key:
        raise LLMNotConfiguredError(
            "未配置 LLM API Key，请在前端「模型设置」或 config.yaml 中填写 api_key。"
        )

    # 优先尝试 langchain_openai.ChatOpenAI
    try:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=api_key,
            base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
            temperature=settings.LLM_TEMPERATURE,
            timeout=settings.LLM_TIMEOUT,
            max_retries=settings.LLM_MAX_RETRIES,
            streaming=True,
        )
    except ImportError:
        # 尝试 langchain.chat_models
        try:
            from langchain.chat_models import init_chat_model

            return init_chat_model(
                model=settings.LLM_MODEL,
                model_provider=settings.LLM_PROVIDER,
                api_key=api_key,
                base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
                temperature=settings.LLM_TEMPERATURE,
                timeout=settings.LLM_TIMEOUT,
                max_retries=settings.LLM_MAX_RETRIES,
            )
        except Exception as e:
            raise RuntimeError(f"无法初始化聊天模型，请确保安装了 langchain-openai 或 langchain: {e}")
