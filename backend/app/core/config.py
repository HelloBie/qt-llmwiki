from functools import lru_cache
from typing import List, Optional, Any, Union
from pathlib import Path
import os
import json

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# 寻找 .env 默认路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """全局应用配置"""
    # 基础信息
    APP_NAME: str = Field(default="qtllmwiki-api", description="服务名称")
    APP_ENV: str = Field(default="dev", description="运行环境: dev / test / prod")
    DEBUG: bool = Field(default=True, description="是否开启调试模式")
    API_PREFIX: str = Field(default="/api/v1", description="接口前缀")
    HOST: str = Field(default="127.0.0.1", description="绑定地址")
    PORT: int = Field(default=8000, description="端口号")

    # 跨域设置 (支持逗号分隔字符串或列表)
    CORS_ORIGINS: Union[List[str], str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        description="允许跨域的来源"
    )

    # LLM 与 Agent 配置
    LLM_PROVIDER: str = Field(default="openai", description="大模型协议提供商")
    LLM_MODEL: str = Field(default="deepseek-chat", description="模型标识符")
    LLM_API_KEY: Optional[str] = Field(default=None, description="API Key")
    LLM_BASE_URL: Optional[str] = Field(default="https://api.deepseek.com/v1", description="模型基础 URL")
    LLM_TEMPERATURE: float = Field(default=0.2, description="采样温度")
    LLM_TIMEOUT: float = Field(default=60.0, description="单次请求超时时间(秒)")
    LLM_MAX_RETRIES: int = Field(default=2, description="重试次数")

    AGENT_MAX_ITERATIONS: int = Field(default=8, description="智能体最大迭代轮数")
    SYSTEM_PROMPT: str = Field(
        default=(
            "你是一个专业、严谨且热情的 AI 助手。回答问题时请先给出核心结论，再展开具体依据。"
            "不确定或不知道的内容切勿凭空编造，请使用中文回答。"
        ),
        description="全局系统提示词"
    )

    model_config = SettingsConfigDict(
        env_file=str(DEFAULT_ENV_FILE) if DEFAULT_ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_strip = v.strip()
            if v_strip.startswith("[") and v_strip.endswith("]"):
                try:
                    return json.loads(v_strip)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_llm_configured(self) -> bool:
        """检查是否配置了可用的 LLM API Key"""
        key = self.LLM_API_KEY or os.environ.get("OPENAI_API_KEY")
        return bool(key and key.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取单例配置实例"""
    return Settings()
