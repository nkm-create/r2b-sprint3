"""認証関連スキーマ"""
from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.models.enums import UserRole
from app.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    """ログインリクエスト"""
    email: EmailStr
    password: str


class LoginResponse(BaseSchema):
    """ログインレスポンス"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒


class TokenPayload(BaseSchema):
    """JWTペイロード"""
    sub: str  # user_id
    exp: datetime
    iat: datetime
    role: UserRole


class RefreshTokenRequest(BaseSchema):
    """トークンリフレッシュリクエスト"""
    refresh_token: str


class CurrentUser(BaseSchema):
    """現在のユーザー情報"""
    user_id: UUID
    email: EmailStr
    name: str
    role: UserRole
    force_password_change: bool


class PasswordResetRequest(BaseSchema):
    """パスワードリセットリクエスト"""
    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    """パスワードリセット確認"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
