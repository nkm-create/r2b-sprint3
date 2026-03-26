"""FastAPI アプリケーション入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API ルーター登録
app.include_router(api_router)


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {"message": "学習塾時間割最適化システム API Ready"}


@app.get("/api/v1/db-test", tags=["Health"])
async def db_test():
    """Database 接続テスト"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return {"status": "Database connected", "result": result.scalar()}
    except Exception as e:
        return {"status": "Database connection failed", "error": str(e)}
