"""テストユーザー作成スクリプト"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models import User, UserRole, UserStatus


async def seed_test_user():
    """テストユーザーを作成"""
    async with AsyncSessionLocal() as session:
        # 既存ユーザー確認
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        if result.scalar_one_or_none():
            print("テストユーザーは既に存在します。スキップします。")
            return

        # テストユーザー作成
        user = User(
            email="admin@example.com",
            password_hash=get_password_hash("password123"),
            name="管理者",
            role=UserRole.SYSTEM_ADMIN,
            status=UserStatus.ACTIVE,
            force_password_change=False,
        )
        session.add(user)
        await session.commit()
        print(f"テストユーザーを作成しました:")
        print(f"  Email: admin@example.com")
        print(f"  Password: password123")
        print(f"  Role: {UserRole.SYSTEM_ADMIN.value}")


if __name__ == "__main__":
    asyncio.run(seed_test_user())
