"""ダッシュボード関連スキーマ"""
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class HeatmapStatus(str, Enum):
    """ヒートマップステータス"""
    SURPLUS = "surplus"  # 余裕あり (需給差 >= 2)
    BALANCED = "balanced"  # 適正 (需給差 == 1)
    TIGHT = "tight"  # ギリギリ (需給差 == 0)
    SHORTAGE = "shortage"  # 不足 (需給差 < 0)


class CoverageStatus(str, Enum):
    """カバー率ステータス"""
    SUFFICIENT = "sufficient"  # 充足 (100%以上)
    PARTIAL = "partial"  # やや不足 (70-99%)
    INSUFFICIENT = "insufficient"  # 不足 (70%未満)


class FulfillmentSummary(BaseModel):
    """充足率サマリー"""
    fulfillment_rate: Decimal = Field(..., description="1対2充足率 (%)")
    total_slots: int = Field(..., description="総コマ数")
    one_to_two_slots: int = Field(..., description="1対2コマ数")
    one_to_one_slots: int = Field(..., description="1対1コマ数")


class PersonnelSummary(BaseModel):
    """人員サマリー"""
    teacher_count: int = Field(..., description="講師数")
    student_count: int = Field(..., description="生徒数")


class HeatmapCell(BaseModel):
    """ヒートマップセル"""
    day_of_week: str = Field(..., description="曜日")
    slot_number: int = Field(..., description="限")
    supply: int = Field(..., description="供給枠数（講師数×2）")
    demand: int = Field(..., description="需要人数（生徒数）")
    balance: int = Field(..., description="需給差")
    status: HeatmapStatus = Field(..., description="ステータス")


class HeatmapResponse(BaseModel):
    """人員状況ヒートマップレスポンス"""
    cells: list[HeatmapCell] = Field(default_factory=list, description="ヒートマップセル一覧")


class SubjectCoverage(BaseModel):
    """科目別カバー率"""
    subject_id: str = Field(..., description="科目ID")
    subject_name: str = Field(..., description="科目名")
    grade_category: str = Field(..., description="学年カテゴリ")
    coverage_rate: Decimal = Field(..., description="カバー率 (%)")
    status: CoverageStatus = Field(..., description="ステータス")


class SubjectCoverageResponse(BaseModel):
    """科目別カバー率レスポンス"""
    items: list[SubjectCoverage] = Field(default_factory=list, description="科目カバー率一覧")


class SupplyDemandBalance(BaseModel):
    """需給バランス"""
    category: str = Field(..., description="カテゴリ名")
    demand: int = Field(..., description="生徒需要コマ数")
    supply: int = Field(..., description="講師供給コマ数")
    difference: int = Field(..., description="差分（供給-需要）")


class SupplyDemandResponse(BaseModel):
    """需給バランスレスポンス"""
    items: list[SupplyDemandBalance] = Field(default_factory=list, description="カテゴリ別需給バランス")


class TermInfo(BaseModel):
    """ターム情報"""
    term_id: UUID = Field(..., description="タームID")
    term_name: str = Field(..., description="ターム名")
    start_date: str = Field(..., description="開始日")
    end_date: str = Field(..., description="終了日")
    status: str = Field(..., description="ステータス")
    is_current: bool = Field(False, description="現在のタームか")


class NotificationItem(BaseModel):
    """通知アイテム"""
    notification_id: UUID = Field(..., description="通知ID")
    notification_type: str = Field(..., description="通知種別")
    severity: str = Field(..., description="重要度")
    title: str = Field(..., description="タイトル")
    message: str = Field(..., description="メッセージ")
    link_url: str | None = Field(None, description="リンクURL")
    is_read: bool = Field(False, description="既読フラグ")
    created_at: str = Field(..., description="作成日時")


class NotificationResponse(BaseModel):
    """通知レスポンス"""
    items: list[NotificationItem] = Field(default_factory=list, description="通知一覧")
    unread_count: int = Field(0, description="未読件数")


class DashboardResponse(BaseModel):
    """ダッシュボードレスポンス"""
    classroom_id: UUID = Field(..., description="教室ID")
    classroom_name: str = Field(..., description="教室名")
    fulfillment: FulfillmentSummary = Field(..., description="充足率サマリー")
    personnel: PersonnelSummary = Field(..., description="人員サマリー")
    heatmap: HeatmapResponse = Field(..., description="人員状況ヒートマップ")
    subject_coverage: SubjectCoverageResponse = Field(..., description="科目別カバー率")
    supply_demand: SupplyDemandResponse = Field(..., description="需給バランス")
    current_term: TermInfo | None = Field(None, description="現在のターム")
    next_term: TermInfo | None = Field(None, description="次のターム")
    notifications: NotificationResponse = Field(..., description="通知一覧")
