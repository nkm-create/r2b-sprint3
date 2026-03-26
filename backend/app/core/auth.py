"""認証依存関係"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, UserRole, UserStatus
from app.repositories.users import UserRepository

# Bearer トークン認証スキーム
security = HTTPBearer()


class AuthError(HTTPException):
    """認証エラー"""

    def __init__(self, code: str, message: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": code, "message": message},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """現在のユーザーを取得（認証必須）"""
    token = credentials.credentials

    # トークンをデコード
    payload = decode_token(token)
    if payload is None:
        raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

    # アクセストークンかどうか確認
    if payload.get("type") != "access":
        raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

    # ユーザーIDを取得
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

    # ユーザーを取得
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

    # ステータス確認
    if user.status != UserStatus.ACTIVE:
        raise AuthError("AUTH_002", "このアカウントは無効です")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """アクティブなユーザーを取得"""
    if current_user.status != UserStatus.ACTIVE:
        raise AuthError("AUTH_002", "このアカウントは無効です")
    return current_user


def require_roles(*roles: UserRole):
    """特定のロールを必要とする依存関係を生成"""

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "AUTH_007", "message": "この操作を行う権限がありません"},
            )
        return current_user

    return role_checker


# よく使う依存関係
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_roles(UserRole.SYSTEM_ADMIN))]
ManagerUser = Annotated[
    User,
    Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.AREA_MANAGER, UserRole.CLASSROOM_MANAGER)),
]
