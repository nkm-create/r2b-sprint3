"""SQLAlchemy AsyncSession 設定"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# AsyncEngine 作成
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # SQL ログ出力（DEBUG時のみ）
    future=True,
)

# AsyncSessionLocal 作成
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base クラス（ORM モデルの基底クラス）
Base = declarative_base()


async def get_db():
    """Database session の取得（依存注入用）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
