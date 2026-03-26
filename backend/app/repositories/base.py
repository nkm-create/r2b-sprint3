"""ベースリポジトリ"""
from typing import Any, Generic, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """汎用的なCRUD操作を提供するベースリポジトリ"""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID | str, *, id_field: str = "id") -> ModelType | None:
        """IDでエンティティを取得"""
        stmt = select(self.model).where(getattr(self.model, id_field) == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[ModelType]:
        """全エンティティを取得（ページネーション対応）"""
        stmt = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, *, filters: dict[str, Any] | None = None) -> int:
        """エンティティの件数を取得"""
        stmt = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """エンティティを作成"""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: dict[str, Any],
    ) -> ModelType:
        """エンティティを更新"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """エンティティを削除（物理削除）"""
        await self.session.delete(db_obj)
        await self.session.flush()

    async def soft_delete(self, db_obj: ModelType) -> ModelType:
        """エンティティを論理削除（deleted_atをセット）"""
        from datetime import datetime, timezone

        if hasattr(db_obj, "deleted_at"):
            setattr(db_obj, "deleted_at", datetime.now(timezone.utc))
            self.session.add(db_obj)
            await self.session.flush()
            await self.session.refresh(db_obj)
        return db_obj

    async def exists(self, id: UUID | str, *, id_field: str = "id") -> bool:
        """エンティティが存在するか確認"""
        stmt = select(func.count()).select_from(self.model).where(
            getattr(self.model, id_field) == id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0
