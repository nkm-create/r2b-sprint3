"""ダッシュボードサービス"""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.classrooms import Classroom, ClassroomSettings
from app.models.enums import (
    DayOfWeek,
    GradeCategory,
    ScheduleStatus,
    SlotType,
    StudentPreferenceValue,
    StudentStatus,
    TeacherPreferenceValue,
    TeacherStatus,
    TermStatus,
)
from app.models.notifications import Notification
from app.models.preferences import StudentPreference, TeacherShiftPreference
from app.models.schedules import Schedule, ScheduleSlot, Term
from app.models.students import Student, StudentSubject
from app.models.subjects import Subject
from app.models.teachers import Teacher, TeacherSubject
from app.schemas.dashboard import (
    CoverageStatus,
    DashboardResponse,
    FulfillmentSummary,
    HeatmapCell,
    HeatmapResponse,
    HeatmapStatus,
    NotificationItem,
    NotificationResponse,
    PersonnelSummary,
    SubjectCoverage,
    SubjectCoverageResponse,
    SupplyDemandBalance,
    SupplyDemandResponse,
    TermInfo,
)


class DashboardService:
    """ダッシュボードサービス"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard(self, classroom_id: UUID, user_id: UUID) -> DashboardResponse:
        """ダッシュボードデータを取得"""
        # 教室情報を取得
        classroom = await self._get_classroom(classroom_id)

        # 現在のタームを取得
        current_term, next_term = await self._get_terms(classroom_id)

        # 各種サマリーを計算
        fulfillment = await self._calculate_fulfillment(classroom_id, current_term)
        personnel = await self._get_personnel_summary(classroom_id)
        heatmap = await self._calculate_heatmap(classroom_id, current_term)
        subject_coverage = await self._calculate_subject_coverage(classroom_id, current_term)
        supply_demand = await self._calculate_supply_demand(classroom_id)
        notifications = await self._get_notifications(user_id, classroom_id)

        return DashboardResponse(
            classroom_id=classroom.classroom_id,
            classroom_name=classroom.classroom_name,
            fulfillment=fulfillment,
            personnel=personnel,
            heatmap=heatmap,
            subject_coverage=subject_coverage,
            supply_demand=supply_demand,
            current_term=current_term,
            next_term=next_term,
            notifications=notifications,
        )

    async def _get_classroom(self, classroom_id: UUID) -> Classroom:
        """教室情報を取得"""
        query = select(Classroom).where(Classroom.classroom_id == classroom_id)
        result = await self.db.execute(query)
        classroom = result.scalar_one_or_none()
        if not classroom:
            raise ValueError(f"Classroom not found: {classroom_id}")
        return classroom

    async def _get_terms(self, classroom_id: UUID) -> tuple[TermInfo | None, TermInfo | None]:
        """現在と次のタームを取得"""
        today = date.today()

        # 現在のターム（進行中）
        query = select(Term).where(
            and_(
                Term.classroom_id == classroom_id,
                Term.start_date <= today,
                Term.end_date >= today,
                Term.deleted_at.is_(None),
            )
        ).order_by(Term.start_date)
        result = await self.db.execute(query)
        current = result.scalar_one_or_none()

        # 次のターム（未来）
        query = select(Term).where(
            and_(
                Term.classroom_id == classroom_id,
                Term.start_date > today,
                Term.deleted_at.is_(None),
            )
        ).order_by(Term.start_date).limit(1)
        result = await self.db.execute(query)
        next_term = result.scalar_one_or_none()

        def to_term_info(term: Term | None, is_current: bool) -> TermInfo | None:
            if not term:
                return None
            return TermInfo(
                term_id=term.term_id,
                term_name=term.term_name,
                start_date=term.start_date.isoformat(),
                end_date=term.end_date.isoformat(),
                status=term.status.value,
                is_current=is_current,
            )

        return to_term_info(current, True), to_term_info(next_term, False)

    async def _calculate_fulfillment(
        self, classroom_id: UUID, current_term: TermInfo | None
    ) -> FulfillmentSummary:
        """充足率を計算"""
        if not current_term:
            return FulfillmentSummary(
                fulfillment_rate=Decimal("0"),
                total_slots=0,
                one_to_two_slots=0,
                one_to_one_slots=0,
            )

        # 確定済みの時間割からコマ数を集計
        query = (
            select(
                func.count(ScheduleSlot.slot_id).label("total"),
                func.count(
                    func.nullif(ScheduleSlot.slot_type != SlotType.ONE_TO_TWO, True)
                ).label("one_to_two"),
            )
            .join(Schedule, Schedule.schedule_id == ScheduleSlot.schedule_id)
            .where(
                and_(
                    Schedule.term_id == current_term.term_id,
                    Schedule.status == ScheduleStatus.CONFIRMED,
                )
            )
        )
        result = await self.db.execute(query)
        row = result.one()

        total_slots = row.total or 0
        one_to_two_slots = row.one_to_two or 0
        one_to_one_slots = total_slots - one_to_two_slots

        if total_slots == 0:
            fulfillment_rate = Decimal("0")
        else:
            # 1対2コマ × 2人 / 総生徒コマ数
            fulfillment_rate = Decimal(one_to_two_slots * 2) / Decimal(
                one_to_two_slots * 2 + one_to_one_slots
            ) * 100

        return FulfillmentSummary(
            fulfillment_rate=fulfillment_rate.quantize(Decimal("0.01")),
            total_slots=total_slots,
            one_to_two_slots=one_to_two_slots,
            one_to_one_slots=one_to_one_slots,
        )

    async def _get_personnel_summary(self, classroom_id: UUID) -> PersonnelSummary:
        """人員サマリーを取得"""
        # アクティブな講師数
        teacher_query = select(func.count(Teacher.teacher_version_id)).where(
            and_(
                Teacher.classroom_id == classroom_id,
                Teacher.is_current == True,
                Teacher.status == TeacherStatus.ACTIVE,
                Teacher.deleted_at.is_(None),
            )
        )
        teacher_result = await self.db.execute(teacher_query)
        teacher_count = teacher_result.scalar() or 0

        # アクティブな生徒数
        student_query = select(func.count(Student.student_version_id)).where(
            and_(
                Student.classroom_id == classroom_id,
                Student.is_current == True,
                Student.status == StudentStatus.ACTIVE,
                Student.deleted_at.is_(None),
            )
        )
        student_result = await self.db.execute(student_query)
        student_count = student_result.scalar() or 0

        return PersonnelSummary(
            teacher_count=teacher_count,
            student_count=student_count,
        )

    async def _calculate_heatmap(
        self, classroom_id: UUID, current_term: TermInfo | None
    ) -> HeatmapResponse:
        """人員状況ヒートマップを計算"""
        if not current_term:
            return HeatmapResponse(cells=[])

        cells = []
        days = [DayOfWeek.MON, DayOfWeek.TUE, DayOfWeek.WED, DayOfWeek.THU, DayOfWeek.FRI, DayOfWeek.SAT]
        slots = [1, 2, 3, 4]

        for day in days:
            slot_range = [0, 1, 2, 3, 4] if day == DayOfWeek.SAT else slots
            for slot in slot_range:
                # 供給: その枠で勤務可能な講師数 × 2
                supply_query = select(func.count(TeacherShiftPreference.preference_id)).where(
                    and_(
                        TeacherShiftPreference.classroom_id == classroom_id,
                        TeacherShiftPreference.term_id == current_term.term_id,
                        TeacherShiftPreference.day_of_week == day,
                        TeacherShiftPreference.slot_number == slot,
                        TeacherShiftPreference.preference_value == TeacherPreferenceValue.AVAILABLE,
                    )
                )
                supply_result = await self.db.execute(supply_query)
                teacher_count = supply_result.scalar() or 0
                supply = teacher_count * 2

                # 需要: その枠で受講可能な生徒数
                demand_query = select(func.count(StudentPreference.preference_id)).where(
                    and_(
                        StudentPreference.classroom_id == classroom_id,
                        StudentPreference.term_id == current_term.term_id,
                        StudentPreference.day_of_week == day,
                        StudentPreference.slot_number == slot,
                        StudentPreference.preference_value.in_([
                            StudentPreferenceValue.PREFERRED,
                            StudentPreferenceValue.POSSIBLE,
                        ]),
                    )
                )
                demand_result = await self.db.execute(demand_query)
                demand = demand_result.scalar() or 0

                balance = supply - demand

                # ステータス判定
                if balance >= 2:
                    status = HeatmapStatus.SURPLUS
                elif balance == 1:
                    status = HeatmapStatus.BALANCED
                elif balance == 0:
                    status = HeatmapStatus.TIGHT
                else:
                    status = HeatmapStatus.SHORTAGE

                cells.append(
                    HeatmapCell(
                        day_of_week=day.value,
                        slot_number=slot,
                        supply=supply,
                        demand=demand,
                        balance=balance,
                        status=status,
                    )
                )

        return HeatmapResponse(cells=cells)

    async def _calculate_subject_coverage(
        self, classroom_id: UUID, current_term: TermInfo | None
    ) -> SubjectCoverageResponse:
        """科目別カバー率を計算"""
        if not current_term:
            return SubjectCoverageResponse(items=[])

        # 科目一覧を取得
        subject_query = select(Subject)
        subject_result = await self.db.execute(subject_query)
        subjects = subject_result.scalars().all()

        # 各科目の需要（生徒が受講希望している科目別コマ数合計）
        demand_query = (
            select(
                StudentSubject.subject_id,
                func.sum(StudentSubject.slots_per_week).label("demand"),
            )
            .join(Student, Student.student_version_id == StudentSubject.student_version_id)
            .where(
                and_(
                    Student.classroom_id == classroom_id,
                    Student.is_current == True,
                    Student.status == StudentStatus.ACTIVE,
                    Student.deleted_at.is_(None),
                )
            )
            .group_by(StudentSubject.subject_id)
        )
        demand_result = await self.db.execute(demand_query)
        demand_by_subject = {row.subject_id: row.demand for row in demand_result}

        # 各科目を教えられる講師数
        supply_query = (
            select(
                TeacherSubject.subject_id,
                func.count(TeacherSubject.teacher_version_id).label("teacher_count"),
            )
            .join(Teacher, Teacher.teacher_version_id == TeacherSubject.teacher_version_id)
            .where(
                and_(
                    Teacher.classroom_id == classroom_id,
                    Teacher.is_current == True,
                    Teacher.status == TeacherStatus.ACTIVE,
                    Teacher.deleted_at.is_(None),
                )
            )
            .group_by(TeacherSubject.subject_id)
        )
        supply_result = await self.db.execute(supply_query)
        supply_by_subject = {row.subject_id: row.teacher_count for row in supply_result}

        # 講師の週あたり最大コマ数を取得
        avg_slots_query = select(func.avg(Teacher.max_slots_per_week)).where(
            and_(
                Teacher.classroom_id == classroom_id,
                Teacher.is_current == True,
                Teacher.status == TeacherStatus.ACTIVE,
                Teacher.deleted_at.is_(None),
            )
        )
        avg_result = await self.db.execute(avg_slots_query)
        avg_slots = avg_result.scalar() or Decimal("0")

        items = []
        for subject in subjects:
            demand = demand_by_subject.get(subject.subject_id, 0)
            teacher_count = supply_by_subject.get(subject.subject_id, 0)

            if demand == 0:
                coverage_rate = Decimal("100")
            else:
                # 供給 = 講師数 × 平均週コマ数
                supply = Decimal(teacher_count) * avg_slots
                coverage_rate = min(Decimal("100"), (supply / Decimal(demand)) * 100)

            # ステータス判定
            if coverage_rate >= 100:
                status = CoverageStatus.SUFFICIENT
            elif coverage_rate >= 70:
                status = CoverageStatus.PARTIAL
            else:
                status = CoverageStatus.INSUFFICIENT

            items.append(
                SubjectCoverage(
                    subject_id=subject.subject_id,
                    subject_name=subject.subject_name,
                    grade_category=subject.grade_category.value,
                    coverage_rate=coverage_rate.quantize(Decimal("0.01")),
                    status=status,
                )
            )

        return SubjectCoverageResponse(items=items)

    async def _calculate_supply_demand(self, classroom_id: UUID) -> SupplyDemandResponse:
        """需給バランスを計算"""
        # カテゴリ別の需要（生徒のコマ数合計）
        demand_query = (
            select(
                Subject.grade_category,
                func.sum(StudentSubject.slots_per_week).label("demand"),
            )
            .join(Subject, Subject.subject_id == StudentSubject.subject_id)
            .join(Student, Student.student_version_id == StudentSubject.student_version_id)
            .where(
                and_(
                    Student.classroom_id == classroom_id,
                    Student.is_current == True,
                    Student.status == StudentStatus.ACTIVE,
                    Student.deleted_at.is_(None),
                )
            )
            .group_by(Subject.grade_category)
        )
        demand_result = await self.db.execute(demand_query)
        demand_by_category = {row.grade_category: row.demand for row in demand_result}

        # カテゴリ別の供給（講師の最大コマ数合計）
        # 講師が複数科目を教える場合は按分が必要だが、簡略化のため講師の最大コマ数を集計
        supply_query = (
            select(func.sum(Teacher.max_slots_per_week).label("supply"))
            .where(
                and_(
                    Teacher.classroom_id == classroom_id,
                    Teacher.is_current == True,
                    Teacher.status == TeacherStatus.ACTIVE,
                    Teacher.deleted_at.is_(None),
                )
            )
        )
        supply_result = await self.db.execute(supply_query)
        total_supply = supply_result.scalar() or 0

        # 各カテゴリの需要比率で供給を按分
        total_demand = sum(demand_by_category.values()) or 1

        items = []
        category_names = {
            GradeCategory.ELEMENTARY: "小学生",
            GradeCategory.JUNIOR_HIGH: "中学生",
            GradeCategory.HIGH_SCHOOL: "高校生",
        }

        for category in GradeCategory:
            demand = demand_by_category.get(category, 0)
            # 需要比率で供給を按分
            supply = int(total_supply * (demand / total_demand)) if total_demand > 0 else 0
            difference = supply - demand

            items.append(
                SupplyDemandBalance(
                    category=category_names.get(category, category.value),
                    demand=demand,
                    supply=supply,
                    difference=difference,
                )
            )

        return SupplyDemandResponse(items=items)

    async def _get_notifications(
        self, user_id: UUID, classroom_id: UUID
    ) -> NotificationResponse:
        """通知一覧を取得"""
        query = (
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    (Notification.classroom_id == classroom_id) | (Notification.classroom_id.is_(None)),
                )
            )
            .order_by(Notification.created_at.desc())
            .limit(10)
        )
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        # 未読件数
        unread_query = select(func.count(Notification.notification_id)).where(
            and_(
                Notification.user_id == user_id,
                (Notification.classroom_id == classroom_id) | (Notification.classroom_id.is_(None)),
                Notification.is_read == False,
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        items = [
            NotificationItem(
                notification_id=n.notification_id,
                notification_type=n.notification_type.value,
                severity=n.severity.value,
                title=n.title,
                message=n.message,
                link_url=n.link_url,
                is_read=n.is_read,
                created_at=n.created_at.isoformat(),
            )
            for n in notifications
        ]

        return NotificationResponse(items=items, unread_count=unread_count)
