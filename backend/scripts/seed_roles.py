"""エリアマネージャー・教室長のテストユーザー作成スクリプト"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models import User, UserRole, UserStatus
from app.models.classrooms import Area, Classroom, UserArea, UserClassroom
from app.models.enums import ClassroomStatus


async def seed_roles():
    async with AsyncSessionLocal() as session:
        # --- エリア作成 ---
        result = await session.execute(select(Area).where(Area.area_name == "東京エリア"))
        area = result.scalar_one_or_none()
        if not area:
            area = Area(area_name="東京エリア")
            session.add(area)
            await session.flush()
            print(f"エリアを作成しました: {area.area_name} (ID: {area.area_id})")
        else:
            print("エリアは既に存在します。スキップします。")

        # --- 教室作成 ---
        result = await session.execute(
            select(Classroom).where(Classroom.classroom_code == "TKY001")
        )
        classroom = result.scalar_one_or_none()
        if not classroom:
            classroom = Classroom(
                area_id=area.area_id,
                classroom_code="TKY001",
                classroom_name="渋谷教室",
                status=ClassroomStatus.OPERATING,
            )
            session.add(classroom)
            await session.flush()
            print(f"教室を作成しました: {classroom.classroom_name} (ID: {classroom.classroom_id})")
        else:
            print("教室は既に存在します。スキップします。")

        # --- エリアマネージャー作成 ---
        result = await session.execute(
            select(User).where(User.email == "area_manager@example.com")
        )
        if not result.scalar_one_or_none():
            area_manager = User(
                email="area_manager@example.com",
                password_hash=get_password_hash("password123"),
                name="エリアマネージャー",
                role=UserRole.AREA_MANAGER,
                status=UserStatus.ACTIVE,
                force_password_change=False,
            )
            session.add(area_manager)
            await session.flush()

            # エリアとの紐付け
            user_area = UserArea(user_id=area_manager.user_id, area_id=area.area_id)
            session.add(user_area)

            print(f"エリアマネージャーを作成しました:")
            print(f"  Email: area_manager@example.com")
            print(f"  Password: password123")
            print(f"  Role: {UserRole.AREA_MANAGER.value}")
        else:
            print("エリアマネージャーは既に存在します。スキップします。")

        # --- 教室長作成 ---
        result = await session.execute(
            select(User).where(User.email == "classroom_manager@example.com")
        )
        if not result.scalar_one_or_none():
            classroom_manager = User(
                email="classroom_manager@example.com",
                password_hash=get_password_hash("password123"),
                name="教室長",
                role=UserRole.CLASSROOM_MANAGER,
                status=UserStatus.ACTIVE,
                force_password_change=False,
            )
            session.add(classroom_manager)
            await session.flush()

            # 教室との紐付け
            user_classroom = UserClassroom(
                user_id=classroom_manager.user_id,
                classroom_id=classroom.classroom_id,
            )
            session.add(user_classroom)

            print(f"教室長を作成しました:")
            print(f"  Email: classroom_manager@example.com")
            print(f"  Password: password123")
            print(f"  Role: {UserRole.CLASSROOM_MANAGER.value}")
        else:
            print("教室長は既に存在します。スキップします。")

        await session.commit()
        print("\n完了しました。")


if __name__ == "__main__":
    asyncio.run(seed_roles())
