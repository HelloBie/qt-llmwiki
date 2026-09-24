import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import Settings, get_settings
from app.core.yaml_config import sync_yaml_to_settings
from app.api.v1.router import api_v1_router
from app.agents.runtime import AgentRuntime

FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app(custom_settings: Optional[Settings] = None, custom_runtime: Optional[AgentRuntime] = None) -> FastAPI:
    """FastAPI 应用工厂函数"""
    settings = custom_settings or get_settings()
    # 自动从 config.yaml 同步模型配置（仅在默认全局单例启动时）
    if custom_settings is None:
        try:
            sync_yaml_to_settings(settings)
        except Exception:
            pass
        try:
            from app.db.doc_records import init_db
            init_db()
        except Exception:
            pass

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="FastAPI + LangGraph + Vue 3 智能知识库脚手架服务",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 注入单例到 app.state
    app.state.settings = settings
    app.state.runtime = custom_runtime or AgentRuntime(settings=settings)

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册根路径信息与基础探针
    @app.get("/", summary="服务元信息")
    async def root_info():
        return {
            "app": settings.APP_NAME,
            "version": "0.1.0",
            "env": settings.APP_ENV,
            "docs": "/docs",
            "api_prefix": settings.API_PREFIX,
        }

    @app.get("/health", summary="根路径存活探针")
    async def root_health():
        return {"status": "ok", "app": settings.APP_NAME}

    # 挂载业务路由
    app.include_router(api_v1_router, prefix=settings.API_PREFIX)

    # 若前端 dist 构建目录存在，挂载静态文件支持单服务模式
    if FRONTEND_DIST_DIR.exists() and (FRONTEND_DIST_DIR / "index.html").is_file():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            target = FRONTEND_DIST_DIR / full_path
            if target.is_file():
                return FileResponse(str(target))
            return FileResponse(str(FRONTEND_DIST_DIR / "index.html"))

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    cfg = get_settings()
    uvicorn.run(
        "app.main:app",
        host=cfg.HOST,
        port=cfg.PORT,
        reload=cfg.DEBUG,
    )
