"""API v1 ルーター"""
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api")

# 認証
api_router.include_router(auth_router)

# ダッシュボード
api_router.include_router(dashboard_router)
