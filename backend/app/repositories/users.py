"""ユーザーリポジトリ"""
from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID
import hashlib

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, RefreshToken, PasswordResetToken
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """ユーザーリポジトリ"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得"""
        stmt = select(User).where(
            and_(
                User.email == email,
                User.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """IDでユーザーを取得"""
        stmt = select(User).where(
            and_(
                User.user_id == user_id,
                User.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_login_failed_count(self, user_id: UUID) -> None:
        """ログイン失敗回数をインクリメント"""
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                login_failed_count=User.login_failed_count + 1,
                locked_until=select(
                    # 5回目の失敗時に30分ロック
                ).scalar_subquery()
            )
        )
        # 5回以上失敗した場合はロック
        user = await self.get_by_id(user_id)
        if user and user.login_failed_count >= 4:  # 次で5回目
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        if user:
            user.login_failed_count += 1
            self.session.add(user)
            await self.session.flush()

    async def reset_login_failed_count(self, user_id: UUID) -> None:
        """ログイン成功時にカウンターをリセット"""
        user = await self.get_by_id(user_id)
        if user:
            user.login_failed_count = 0
            user.locked_until = None
            user.last_login_at = datetime.now(timezone.utc)
            self.session.add(user)
            await self.session.flush()

    async def update_password(
        self,
        user_id: UUID,
        password_hash: str,
        force_password_change: bool = False,
    ) -> None:
        """パスワードを更新"""
        user = await self.get_by_id(user_id)
        if user:
            user.password_hash = password_hash
            user.force_password_change = force_password_change
            user.login_failed_count = 0
            user.locked_until = None
            self.session.add(user)
            await self.session.flush()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """リフレッシュトークンリポジトリ"""

    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)

    @staticmethod
    def hash_token(token: str) -> str:
        """トークンをハッシュ化"""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_token(
        self,
        user_id: UUID,
        token: str,
        expires_at: datetime,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """リフレッシュトークンを作成"""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=self.hash_token(token),
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        await self.session.refresh(refresh_token)
        return refresh_token

    async def get_valid_token(self, token: str) -> RefreshToken | None:
        """有効なリフレッシュトークンを取得"""
        token_hash = self.hash_token(token)
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.expires_at > datetime.now(timezone.utc),
                RefreshToken.is_revoked == False,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_token(self, token: str) -> None:
        """トークンを失効させる"""
        token_hash = self.hash_token(token)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """ユーザーの全トークンを失効させる"""
        stmt = (
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False,
                )
            )
            .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)
        await self.session.flush()


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """パスワードリセットトークンリポジトリ"""

    def __init__(self, session: AsyncSession):
        super().__init__(PasswordResetToken, session)

    @staticmethod
    def hash_token(token: str) -> str:
        """トークンをハッシュ化"""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_token(
        self,
        user_id: UUID,
        token: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """パスワードリセットトークンを作成"""
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=self.hash_token(token),
            expires_at=expires_at,
        )
        self.session.add(reset_token)
        await self.session.flush()
        await self.session.refresh(reset_token)
        return reset_token

    async def get_valid_token(self, token: str) -> PasswordResetToken | None:
        """有効なリセットトークンを取得"""
        token_hash = self.hash_token(token)
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
                PasswordResetToken.used_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_as_used(self, token: str) -> None:
        """トークンを使用済みにする"""
        token_hash = self.hash_token(token)
        stmt = (
            update(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hash)
            .values(used_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)
        await self.session.flush()
