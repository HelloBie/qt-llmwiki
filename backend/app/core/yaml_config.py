import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from app.core.config import Settings, get_settings

# 定位 config.yaml 物理位置在 backend/config.yaml
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_YAML_PATH = BACKEND_DIR / "config.yaml"


def get_default_config_dict(settings: Optional[Settings] = None) -> Dict[str, Any]:
    """生成默认配置字典结构"""
    s = settings or get_settings()
    return {
        "openai": {
            "base_url": s.LLM_BASE_URL or "https://api.deepseek.com/v1",
            "api_key": s.LLM_API_KEY or "",
            "model": s.LLM_MODEL or "deepseek-chat",
            "temperature": float(s.LLM_TEMPERATURE),
            "max_tokens": 4096,
            "top_p": 1.0,
            "organization": "",
            "project_id": "",
        },
        "models": {
            "chat": {
                "name": s.LLM_MODEL or "deepseek-chat",
                "base_url": "",
                "api_key": "",
                "temperature": float(s.LLM_TEMPERATURE),
                "max_tokens": 4096,
                "description": "主问答对话模型，面向用户交互，负责综合推理与高质量解答",
            },
            "digest": {
                "name": "qwen-plus",
                "base_url": "",
                "api_key": "",
                "temperature": 0.3,
                "max_tokens": 4096,
                "description": "文件消化解析模型，负责文档解析、知识库构建与实体结构化提炼",
            },
            "embedding": {
                "name": s.LOCAL_EMBEDDING_MODEL or "bge-m3",
                "base_url": s.OLLAMA_BASE_URL or "http://localhost:11434/v1",
                "api_key": "ollama",
                "dimension": 1024,
                "description": "向量嵌入模型，负责知识库文档切片语义编码与相似度检索",
            },
            "rerank": {
                "name": s.LOCAL_RERANK_MODEL or "bge-reranker-v2-m3",
                "base_url": s.OLLAMA_BASE_URL or "http://localhost:11434",
                "api_key": "ollama",
                "top_n": 5,
                "description": "语义重排模型，负责候选文本块 Cross-Encoder 精准打分与过滤",
            },
            "expansion": {
                "name": s.LOCAL_EXPANSION_MODEL or "qwen2.5:1.5b",
                "base_url": s.OLLAMA_BASE_URL or "http://localhost:11434/v1",
                "api_key": "ollama",
                "temperature": 0.3,
                "description": "查询扩展模型，负责用户提问多角度改写与关键词提取",
            },
        },
        "server": {
            "host": s.HOST,
            "port": s.PORT,
            "app_name": s.APP_NAME,
            "debug": s.DEBUG,
        },
    }


def load_yaml_config() -> Dict[str, Any]:
    """从 config.yaml 加载配置，若不存在则自动初始化"""
    if not CONFIG_YAML_PATH.is_file():
        default_cfg = get_default_config_dict()
        save_yaml_config(default_cfg)
        return default_cfg

    try:
        with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                data = get_default_config_dict()
                save_yaml_config(data)
            return data
    except Exception as e:
        print(f"[WARN] 读取 config.yaml 异常: {e}，使用默认配置")
        return get_default_config_dict()


def save_yaml_config(config_data: Dict[str, Any]) -> None:
    """将配置字典格式化持久化写入 config.yaml"""
    CONFIG_YAML_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(
            config_data,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        )


def sync_yaml_to_settings(settings: Settings) -> None:
    """将 config.yaml 中的最新配置同步更新至内存 Settings 单例中"""
    cfg = load_yaml_config()
    openai_cfg = cfg.get("openai", {})
    models_cfg = cfg.get("models", {})

    chat_cfg = models_cfg.get("chat", {})
    if chat_cfg.get("name"):
        settings.LLM_MODEL = chat_cfg["name"]
    elif "model" in openai_cfg:
        settings.LLM_MODEL = openai_cfg["model"]

    if chat_cfg.get("base_url"):
        settings.LLM_BASE_URL = chat_cfg["base_url"]
    elif "base_url" in openai_cfg:
        settings.LLM_BASE_URL = openai_cfg["base_url"]

    if chat_cfg.get("api_key"):
        settings.LLM_API_KEY = chat_cfg["api_key"]
    elif "api_key" in openai_cfg:
        settings.LLM_API_KEY = openai_cfg["api_key"]

    if "temperature" in chat_cfg:
        settings.LLM_TEMPERATURE = float(chat_cfg["temperature"])
    elif "temperature" in openai_cfg:
        settings.LLM_TEMPERATURE = float(openai_cfg["temperature"])

    # 本地小模型同步
    if "embedding" in models_cfg and models_cfg["embedding"].get("name"):
        settings.LOCAL_EMBEDDING_MODEL = models_cfg["embedding"]["name"]
    if "rerank" in models_cfg and models_cfg["rerank"].get("name"):
        settings.LOCAL_RERANK_MODEL = models_cfg["rerank"]["name"]
    if "expansion" in models_cfg and models_cfg["expansion"].get("name"):
        settings.LOCAL_EXPANSION_MODEL = models_cfg["expansion"]["name"]
