from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.chat import router as chat_router
from app.api.v1.files import router as files_router
from app.api.v1.settings import router as settings_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(files_router)
api_v1_router.include_router(settings_router)
