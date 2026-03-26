"""ダッシュボードAPI"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.users import User
from app.schemas.dashboard import DashboardResponse, NotificationResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/classrooms/{classroom_id}/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """
    ダッシュボードデータを取得

    教室長向けのダッシュボードデータを取得します。
    - 充足率サマリー
    - 人員サマリー
    - 人員状況ヒートマップ
    - 科目別カバー率
    - 需給バランス
    - ターム情報
    - 通知一覧
    """
    # TODO: 教室へのアクセス権限チェック
    service = DashboardService(db)
    try:
        return await service.get_dashboard(classroom_id, current_user.user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/notifications", response_model=NotificationResponse)
async def get_notifications(
    classroom_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """
    通知一覧を取得
    """
    service = DashboardService(db)
    return await service._get_notifications(current_user.user_id, classroom_id)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    classroom_id: UUID,
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    通知を既読にする
    """
    from datetime import datetime, timezone
    from sqlalchemy import update
    from app.models.notifications import Notification

    await db.execute(
        update(Notification)
        .where(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id,
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    await db.commit()

    return {"status": "ok"}
