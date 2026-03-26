"""ベーススキーマ"""
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """全スキーマの基底クラス"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampSchema(BaseSchema):
    """タイムスタンプを含むスキーマ"""
    created_at: datetime
    updated_at: datetime


class SoftDeleteSchema(BaseSchema):
    """論理削除フラグを含むスキーマ"""
    deleted_at: datetime | None = None


# ページネーション用
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """ページネーションレスポンス"""
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class SuccessResponse(BaseModel):
    """成功レスポンス"""
    success: bool = True
    message: str | None = None


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    success: bool = False
    error: str
    detail: str | None = None
