"""ユーザー関連スキーマ"""
from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.enums import UserRole, UserStatus
from app.schemas.base import BaseSchema, SoftDeleteSchema, TimestampSchema


class UserBase(BaseSchema):
    """ユーザー基底スキーマ"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=50)
    role: UserRole


class UserCreate(UserBase):
    """ユーザー作成スキーマ"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """ユーザー更新スキーマ"""
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=1, max_length=50)
    role: UserRole | None = None
    status: UserStatus | None = None


class UserResponse(UserBase, TimestampSchema, SoftDeleteSchema):
    """ユーザーレスポンススキーマ"""
    user_id: UUID
    status: UserStatus
    login_failed_count: int
    locked_until: datetime | None
    force_password_change: bool
    last_login_at: datetime | None


class UserBriefResponse(BaseSchema):
    """ユーザー簡易レスポンススキーマ"""
    user_id: UUID
    email: EmailStr
    name: str
    role: UserRole
    status: UserStatus


class PasswordChange(BaseSchema):
    """パスワード変更スキーマ"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordReset(BaseSchema):
    """パスワードリセットスキーマ"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
