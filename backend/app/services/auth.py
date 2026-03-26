"""認証サービス"""
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models import User, UserStatus, AuditLog
from app.repositories.users import (
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    UserRepository,
)


class AuthError(Exception):
    """認証エラー"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class AuthService:
    """認証サービス"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.refresh_token_repo = RefreshTokenRepository(session)
        self.password_reset_repo = PasswordResetTokenRepository(session)

    async def login(
        self,
        email: str,
        password: str,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> dict:
        """ログイン処理"""
        # ユーザー検索
        user = await self.user_repo.get_by_email(email)
        if user is None:
            raise AuthError("AUTH_001", "メールアドレスまたはパスワードが正しくありません")

        # ステータス確認
        if user.status != UserStatus.ACTIVE or user.deleted_at is not None:
            raise AuthError("AUTH_002", "このアカウントは無効です")

        # アカウントロック確認
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining_minutes = int(
                (user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60
            )
            raise AuthError(
                "AUTH_003",
                f"アカウントがロックされています。{remaining_minutes}分後に再試行してください",
            )

        # パスワード照合
        if not verify_password(password, user.password_hash):
            await self.user_repo.increment_login_failed_count(user.user_id)
            raise AuthError("AUTH_001", "メールアドレスまたはパスワードが正しくありません")

        # 認証成功
        await self.user_repo.reset_login_failed_count(user.user_id)

        # トークン生成
        access_token = create_access_token(
            data={"sub": str(user.user_id), "role": user.role.value}
        )
        refresh_token = create_refresh_token(data={"sub": str(user.user_id)})

        # リフレッシュトークン保存
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.refresh_token_repo.create_token(
            user_id=user.user_id,
            token=refresh_token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )

        # 監査ログ
        audit_log = AuditLog(
            user_id=user.user_id,
            action="LOGIN",
            entity_type="User",
            entity_id=str(user.user_id),
            ip_address=ip_address,
            user_agent=device_info,
        )
        self.session.add(audit_log)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": str(user.user_id),
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "force_password_change": user.force_password_change,
            },
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """アクセストークンをリフレッシュ"""
        # トークン検証
        token_record = await self.refresh_token_repo.get_valid_token(refresh_token)
        if token_record is None:
            raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

        # ユーザー確認
        user = await self.user_repo.get_by_id(token_record.user_id)
        if user is None or user.status != UserStatus.ACTIVE:
            raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

        # 新しいアクセストークン発行
        access_token = create_access_token(
            data={"sub": str(user.user_id), "role": user.role.value}
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def logout(self, refresh_token: str, user_id: UUID) -> None:
        """ログアウト"""
        await self.refresh_token_repo.revoke_token(refresh_token)

        # 監査ログ
        audit_log = AuditLog(
            user_id=user_id,
            action="LOGOUT",
            entity_type="User",
            entity_id=str(user_id),
        )
        self.session.add(audit_log)

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """パスワード変更"""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise AuthError("AUTH_006", "セッションが無効です。再ログインしてください")

        # 現在のパスワード確認
        if not verify_password(current_password, user.password_hash):
            raise AuthError("AUTH_005", "現在のパスワードが正しくありません")

        # パスワード更新
        new_password_hash = get_password_hash(new_password)
        await self.user_repo.update_password(
            user_id=user_id,
            password_hash=new_password_hash,
            force_password_change=False,
        )

        # 全トークン失効
        await self.refresh_token_repo.revoke_all_user_tokens(user_id)

        # 監査ログ
        audit_log = AuditLog(
            user_id=user_id,
            action="UPDATE",
            entity_type="User",
            entity_id=str(user_id),
            new_value={"field": "password"},
        )
        self.session.add(audit_log)

    async def request_password_reset(self, email: str) -> str | None:
        """パスワードリセットリクエスト（トークンを返す）"""
        user = await self.user_repo.get_by_email(email)
        if user is None:
            # セキュリティ上、ユーザーが存在しない場合もNoneを返す
            return None

        # トークン生成（32バイト = 64文字の16進数）
        token = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        await self.password_reset_repo.create_token(
            user_id=user.user_id,
            token=token,
            expires_at=expires_at,
        )

        return token

    async def execute_password_reset(self, token: str, new_password: str) -> None:
        """パスワードリセット実行"""
        # トークン検証
        token_record = await self.password_reset_repo.get_valid_token(token)
        if token_record is None:
            raise AuthError("AUTH_004", "トークンが無効または期限切れです")

        # パスワード更新
        new_password_hash = get_password_hash(new_password)
        await self.user_repo.update_password(
            user_id=token_record.user_id,
            password_hash=new_password_hash,
            force_password_change=False,
        )

        # トークン使用済みにする
        await self.password_reset_repo.mark_as_used(token)

        # 全トークン失効
        await self.refresh_token_repo.revoke_all_user_tokens(token_record.user_id)

        # 監査ログ
        audit_log = AuditLog(
            user_id=token_record.user_id,
            action="UPDATE",
            entity_type="User",
            entity_id=str(token_record.user_id),
            new_value={"field": "password", "via": "password_reset"},
        )
        self.session.add(audit_log)
