from typing import Annotated
from fastapi import Depends, Request
from app.core.config import Settings, get_settings
from app.agents.runtime import AgentRuntime


def get_settings_dep(request: Request) -> Settings:
    """获取应用配置单例，优先使用 app.state 中注入的配置"""
    if hasattr(request.app.state, "settings") and request.app.state.settings is not None:
        return request.app.state.settings
    return get_settings()


def get_runtime_dep(request: Request, settings: Settings = Depends(get_settings_dep)) -> AgentRuntime:
    """从 app.state 中获取或构建 AgentRuntime 单例"""
    if not hasattr(request.app.state, "runtime") or request.app.state.runtime is None:
        request.app.state.runtime = AgentRuntime(settings=settings)
    return request.app.state.runtime


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
RuntimeDep = Annotated[AgentRuntime, Depends(get_runtime_dep)]
