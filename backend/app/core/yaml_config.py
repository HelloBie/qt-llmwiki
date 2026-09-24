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

    if "base_url" in openai_cfg:
        settings.LLM_BASE_URL = openai_cfg["base_url"]
    if "api_key" in openai_cfg:
        settings.LLM_API_KEY = openai_cfg["api_key"]
    if "model" in openai_cfg:
        settings.LLM_MODEL = openai_cfg["model"]
    if "temperature" in openai_cfg:
        settings.LLM_TEMPERATURE = float(openai_cfg["temperature"])
