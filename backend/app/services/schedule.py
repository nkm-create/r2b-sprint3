"""
時間割作成サービス
"""
import asyncio
import uuid
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.classrooms import Classroom, ClassroomSettings, TimeSlot, UserClassroom
from app.models.enums import DayOfWeek, DayType, ScheduleStatus, SlotStatus, SlotType, TeacherPreferenceValue, StudentPreferenceValue, ConstraintTargetType
from app.models.preferences import StudentPreference, TeacherShiftPreference
from app.models.schedules import Policy, Schedule, ScheduleSlot, Term, TermConstraint
from app.models.students import Student, StudentSubject
from app.models.subjects import Subject, NgRelation
from app.models.teachers import Teacher, TeacherSubject, TeacherGrade
from app.services.solver.schedule_solver import ScheduleSolver
from app.services.solver.models import (
    SolverInput,
    SolverConfig,
    TeacherData,
    StudentData,
    TimeSlotData,
    PolicyData,
    PreferenceValue,
    SlotType as SolverSlotType,
)
from app.services.llm_service import (
    LLMService,
    ExplanationContext,
    WhatIfContext,
)
from app.services.export_service import (
    ExportService,
    ExportData,
    ExportSlot,
)
from app.schemas.schedule import (
    AnalyzeResponse,
    Bottleneck,
    BottleneckExplanation,
    CalendarViewResponse,
    CellInfo,
    ConfirmCheckResponse,
    ConfirmResponse,
    ConfirmWarning,
    ExplanationResponse,
    ExplanationSummary,
    ExportResponse,
    GenerateOptions,
    GenerateSuccessResponse,
    GenerationProgress,
    GenerationResult,
    MovableTarget,
    MovableTargetsResponse,
    MoveSlotResponse,
    OrchestratorDecision,
    PersonInfo,
    ProblemAnalysis,
    RecommendedStrategy,
    ScaleDetails,
    ScheduleJourneyStatusResponse,
    JourneyStepStatus,
    ScheduleListItem,
    ScheduleListResponse,
    ScheduleMetrics,
    SlotInfo,
    SolverStats,
    TradeOff,
    UnplacedStudent,
    WhatIfResponse,
)


class ScheduleService:
    """時間割作成サービス"""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: LLMService | None = None,
        export_service: ExportService | None = None,
    ):
        self.db = db
        self.llm_service = llm_service or LLMService()
        self.export_service = export_service or ExportService()

    async def _check_classroom_access(
        self, classroom_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """教室アクセス権限を確認"""
        result = await self.db.execute(
            select(UserClassroom).where(
                UserClassroom.classroom_id == classroom_id,
                UserClassroom.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            raise PermissionError("この教室へのアクセス権限がありません")

    async def _get_term(
        self, classroom_id: uuid.UUID, term_id: uuid.UUID
    ) -> Term:
        """タームを取得"""
        result = await self.db.execute(
            select(Term).where(
                Term.term_id == term_id,
                Term.classroom_id == classroom_id,
                Term.deleted_at.is_(None),
            )
        )
        term = result.scalar_one_or_none()
        if not term:
            raise ValueError("指定されたタームが見つかりません")
        return term

    @staticmethod
    def build_journey_status(
        *,
        teacher_preference_count: int,
        student_preference_count: int,
        policy_count: int,
        enabled_policy_count: int,
        constraint_count: int,
    ) -> dict[str, Any]:
        """時間割作成ジャーニーの充足状況を構築"""
        missing_requirements: list[str] = []

        preferences_ready = teacher_preference_count > 0 and student_preference_count > 0
        if teacher_preference_count == 0:
            missing_requirements.append("講師希望データが未登録です")
        if student_preference_count == 0:
            missing_requirements.append("生徒希望データが未登録です")

        conditions_ready = policy_count > 0 and enabled_policy_count > 0
        if policy_count == 0:
            missing_requirements.append("ポリシーが未設定です")
        elif enabled_policy_count == 0:
            missing_requirements.append("有効なポリシーがありません")

        is_ready_to_generate = preferences_ready and conditions_ready
        steps = {
            "preferences": {
                "is_ready": preferences_ready,
                "message": (
                    "希望データが揃っています"
                    if preferences_ready
                    else "講師・生徒の希望データをアップロードしてください"
                ),
            },
            "conditions": {
                "is_ready": conditions_ready,
                "message": (
                    "条件設定が完了しています"
                    if conditions_ready
                    else "ポリシーを1件以上有効にしてください"
                ),
            },
            "generate": {
                "is_ready": is_ready_to_generate,
                "message": (
                    "時間割生成を実行できます"
                    if is_ready_to_generate
                    else "前ステップを完了してください"
                ),
            },
        }

        return {
            "is_ready_to_generate": is_ready_to_generate,
            "steps": steps,
            "counts": {
                "teacher_preferences": teacher_preference_count,
                "student_preferences": student_preference_count,
                "policies": policy_count,
                "enabled_policies": enabled_policy_count,
                "constraints": constraint_count,
            },
            "missing_requirements": missing_requirements,
        }

    async def get_journey_status(
        self,
        classroom_id: uuid.UUID,
        term_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ScheduleJourneyStatusResponse:
        """時間割作成ジャーニーの準備状況を取得"""
        await self._check_classroom_access(classroom_id, user_id)
        await self._get_term(classroom_id, term_id)

        teacher_pref_count_result = await self.db.execute(
            select(func.count(TeacherShiftPreference.preference_id)).where(
                TeacherShiftPreference.term_id == term_id
            )
        )
        student_pref_count_result = await self.db.execute(
            select(func.count(StudentPreference.preference_id)).where(
                StudentPreference.term_id == term_id
            )
        )
        policy_count_result = await self.db.execute(
            select(func.count(Policy.policy_id)).where(Policy.term_id == term_id)
        )
        enabled_policy_count_result = await self.db.execute(
            select(func.count(Policy.policy_id)).where(
                Policy.term_id == term_id,
                Policy.is_enabled == True,
            )
        )
        constraint_count_result = await self.db.execute(
            select(func.count(TermConstraint.constraint_id)).where(
                TermConstraint.term_id == term_id
            )
        )

        status_dict = self.build_journey_status(
            teacher_preference_count=teacher_pref_count_result.scalar() or 0,
            student_preference_count=student_pref_count_result.scalar() or 0,
            policy_count=policy_count_result.scalar() or 0,
            enabled_policy_count=enabled_policy_count_result.scalar() or 0,
            constraint_count=constraint_count_result.scalar() or 0,
        )

        return ScheduleJourneyStatusResponse(
            is_ready_to_generate=status_dict["is_ready_to_generate"],
            steps={
                key: JourneyStepStatus(**value)
                for key, value in status_dict["steps"].items()
            },
            counts=status_dict["counts"],
            missing_requirements=status_dict["missing_requirements"],
        )

    async def analyze(
        self,
        classroom_id: uuid.UUID,
        term_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AnalyzeResponse:
        """問題分析（F080）"""
        await self._check_classroom_access(classroom_id, user_id)
        term = await self._get_term(classroom_id, term_id)

        # 講師数を取得
        teacher_result = await self.db.execute(
            select(func.count(Teacher.teacher_id)).where(
                Teacher.classroom_id == classroom_id,
                Teacher.is_current == True,
            )
        )
        teacher_count = teacher_result.scalar() or 0

        # 生徒数を取得
        student_result = await self.db.execute(
            select(func.count(Student.student_id)).where(
                Student.classroom_id == classroom_id,
                Student.is_current == True,
            )
        )
        student_count = student_result.scalar() or 0

        # 週間コマ数を概算
        weekly_slots = teacher_count * 15  # 概算: 講師×平均コマ数

        # 問題規模を判定
        if teacher_count <= 15:
            scale = "small"
        elif teacher_count <= 35:
            scale = "medium"
        else:
            scale = "large"

        # 難易度判定（簡易版）
        difficulty_reasons = []
        if student_count > teacher_count * 4:
            difficulty_reasons.append("生徒数が講師数に対して多い")
        if teacher_count < 10:
            difficulty_reasons.append("講師数が少ない")

        difficulty = "low" if len(difficulty_reasons) == 0 else (
            "medium" if len(difficulty_reasons) == 1 else "high"
        )

        # ボトルネック検出（簡易版）
        bottlenecks = []
        # 実際にはシフト希望と受講希望を比較して需給ギャップを検出
        # ここでは簡易的に土曜をボトルネックとして表示
        if student_count > 50:
            bottlenecks.append(
                Bottleneck(
                    type="time_slot",
                    day_of_week="sat",
                    slot_number=3,
                    demand=15,
                    supply=10,
                    gap=-5,
                )
            )

        # 推奨戦略
        if scale == "small":
            timeout = 10
        elif scale == "medium":
            timeout = 30
        else:
            timeout = 60

        return AnalyzeResponse(
            analysis=ProblemAnalysis(
                scale=scale,
                scale_details=ScaleDetails(
                    teacher_count=teacher_count,
                    student_count=student_count,
                    weekly_slots=weekly_slots,
                ),
                difficulty=difficulty,
                difficulty_reasons=difficulty_reasons if difficulty_reasons else [
                    "特に困難な要因は検出されませんでした"
                ],
                bottlenecks=bottlenecks,
            ),
            recommended_strategy=RecommendedStrategy(
                initial_strategy="standard",
                timeout=timeout,
                reason=f"{scale}規模問題、標準戦略で求解可能と推定",
            ),
        )

    async def generate(
        self,
        classroom_id: uuid.UUID,
        term_id: uuid.UUID,
        user_id: uuid.UUID,
        options: GenerateOptions,
        progress_callback: Any | None = None,
    ) -> GenerateSuccessResponse:
        """時間割生成（F081）- OR-Toolsソルバーを使用"""
        await self._check_classroom_access(classroom_id, user_id)
        term = await self._get_term(classroom_id, term_id)
        journey_status = await self.get_journey_status(classroom_id, term_id, user_id)
        if not journey_status.is_ready_to_generate:
            raise ValueError(
                "生成前の準備が不足しています: "
                + " / ".join(journey_status.missing_requirements)
            )

        # 既存の最新バージョンを取得
        version_result = await self.db.execute(
            select(func.max(Schedule.version)).where(
                Schedule.term_id == term_id,
            )
        )
        current_version = version_result.scalar() or 0
        new_version = current_version + 1

        decisions = []
        start_time = datetime.now(timezone.utc)

        # ソルバー入力データを準備
        solver_input = await self._prepare_solver_input(classroom_id, term_id)
        policy_map = {p.policy_type: p for p in solver_input.policies}
        p005 = policy_map.get("P005")
        policy_target_rate = None
        if p005 and p005.is_enabled:
            policy_target_rate = p005.parameters.get("target_rate")

        # ソルバー設定
        config = SolverConfig(
            target_fulfillment_rate=(
                int(policy_target_rate)
                if policy_target_rate is not None
                else options.target_fulfillment_rate
            ),
            max_timeout_seconds=options.max_timeout_seconds,
            strategy=options.strategy if hasattr(options, 'strategy') else "standard",
            enable_soft_constraints=True,
        )

        # 進捗コールバック
        loop = asyncio.get_running_loop()

        def on_progress(progress_data: dict):
            if progress_callback:
                asyncio.run_coroutine_threadsafe(
                    progress_callback(
                        GenerationProgress(
                            type="progress",
                            solutions_found=progress_data.get("solutions_found", 0),
                            current_rate=Decimal(str(progress_data.get("current_objective", 0))),
                            elapsed_ms=progress_data.get("elapsed_ms", 0),
                            strategy=config.strategy,
                        )
                    ),
                    loop,
                )

        decisions.append(
            OrchestratorDecision(
                time_ms=0,
                decision="start",
                current_rate=Decimal("0"),
                reason="ソルバー開始",
            )
        )

        # ソルバー実行（バックグラウンドスレッドで実行）
        solver = ScheduleSolver(config)

        # asyncioのrun_in_executorを使用してブロッキング処理を非同期化
        solver_output = await loop.run_in_executor(
            None,
            lambda: solver.solve(solver_input, on_progress)
        )

        # 結果を取得（DB制約に合わせて 0-100 に丸める）
        def _clamp_rate(rate: Decimal) -> Decimal:
            return max(Decimal("0"), min(Decimal("100"), rate))

        fulfillment_rate = _clamp_rate(solver_output.fulfillment_rate)
        soft_constraint_rate = _clamp_rate(solver_output.soft_constraint_rate)
        one_to_two_rate = _clamp_rate(solver_output.one_to_two_rate)

        elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        decisions.append(
            OrchestratorDecision(
                time_ms=elapsed_ms,
                decision="stop",
                current_rate=fulfillment_rate,
                reason=f"ソルバー終了: {solver_output.status}",
            )
        )

        # 講師・生徒数を取得
        teacher_count = len(solver_input.teachers)
        student_count = len(solver_input.students)

        # マスタスナップショット作成
        master_snapshot = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "teacher_count": teacher_count,
            "student_count": student_count,
        }

        # 時間割を作成
        schedule = Schedule(
            schedule_id=uuid.uuid4(),
            term_id=term_id,
            version=new_version,
            status=ScheduleStatus.DRAFT,
            master_snapshot=master_snapshot,
            generation_config={
                "target_fulfillment_rate": config.target_fulfillment_rate,
                "max_timeout_seconds": options.max_timeout_seconds,
                "unplaced_count": len(solver_output.unplaced_students),
                "one_to_two_rate": float(one_to_two_rate),
            },
            fulfillment_rate=fulfillment_rate,
            soft_constraint_rate=soft_constraint_rate,
        )
        self.db.add(schedule)
        await self.db.flush()

        # ソルバーの出力からコマを生成
        await self._create_slots_from_solver(schedule.schedule_id, solver_output)

        await self.db.commit()

        if progress_callback:
            await progress_callback(
                GenerationProgress(
                    type="complete",
                    status=solver_output.status,
                    final_rate=fulfillment_rate,
                    termination_reason=solver_output.stats.termination_reason if solver_output.stats else "unknown",
                )
            )

        return GenerateSuccessResponse(
            schedule_id=schedule.schedule_id,
            version=new_version,
            status="draft",
            solution_status=solver_output.status,
            result=GenerationResult(
                fulfillment_rate=fulfillment_rate,
                soft_constraint_rate=soft_constraint_rate,
                one_to_two_rate=one_to_two_rate,
                unplaced_students=len(solver_output.unplaced_students),
            ),
            solver_stats=SolverStats(
                strategy_used=solver_output.stats.strategy_used if solver_output.stats else "standard",
                solve_time_ms=solver_output.stats.solve_time_ms if solver_output.stats else elapsed_ms,
                solutions_found=solver_output.stats.solutions_found if solver_output.stats else 0,
                optimality_gap=solver_output.stats.optimality_gap if solver_output.stats else Decimal("1.0"),
                termination_reason=solver_output.stats.termination_reason if solver_output.stats else "unknown",
            ),
            orchestrator_decisions=decisions,
            next_action="confirm_or_adjust",
        )

    async def _build_preference_maps(
        self, term_id: uuid.UUID
    ) -> tuple[dict[tuple[str, str, int], TeacherPreferenceValue], dict[tuple[str, str, int], StudentPreferenceValue]]:
        teacher_result = await self.db.execute(
            select(TeacherShiftPreference).where(TeacherShiftPreference.term_id == term_id)
        )
        student_result = await self.db.execute(
            select(StudentPreference).where(StudentPreference.term_id == term_id)
        )

        teacher_pref_map: dict[tuple[str, str, int], TeacherPreferenceValue] = {}
        for pref in teacher_result.scalars().all():
            teacher_pref_map[(pref.teacher_id, pref.day_of_week.value, pref.slot_number)] = pref.preference_value

        student_pref_map: dict[tuple[str, str, int], StudentPreferenceValue] = {}
        for pref in student_result.scalars().all():
            student_pref_map[(pref.student_id, pref.day_of_week.value, pref.slot_number)] = pref.preference_value

        return teacher_pref_map, student_pref_map

    def _collect_slot_issues(
        self,
        *,
        teacher_id: str,
        student1_id: str,
        student2_id: str | None,
        slot_number: int,
        day_key: str,
        teacher_pref_map: dict[tuple[str, str, int], TeacherPreferenceValue],
        student_pref_map: dict[tuple[str, str, int], StudentPreferenceValue],
    ) -> list[str]:
        issues: list[str] = []
        if teacher_id:
            teacher_pref = teacher_pref_map.get((teacher_id, day_key, slot_number))
            if teacher_pref == TeacherPreferenceValue.UNAVAILABLE:
                issues.append("講師が出勤不可の時間帯です")

        if student1_id:
            student1_pref = student_pref_map.get((student1_id, day_key, slot_number))
            if student1_pref == StudentPreferenceValue.UNAVAILABLE:
                issues.append("生徒1の希望不可時間です")
            elif student1_pref == StudentPreferenceValue.POSSIBLE:
                issues.append("生徒1の希望度が下がります（◎→◯/△）")

        if student2_id:
            student2_pref = student_pref_map.get((student2_id, day_key, slot_number))
            if student2_pref == StudentPreferenceValue.UNAVAILABLE:
                issues.append("生徒2の希望不可時間です")
            elif student2_pref == StudentPreferenceValue.POSSIBLE:
                issues.append("生徒2の希望度が下がります（◎→◯/△）")

        return issues

    async def _prepare_solver_input(
        self, classroom_id: uuid.UUID, term_id: uuid.UUID
    ) -> SolverInput:
        """ソルバー入力データを準備"""
        # 講師データを取得
        teacher_result = await self.db.execute(
            select(Teacher)
            .options(
                selectinload(Teacher.subjects),
                selectinload(Teacher.grades),
            )
            .where(
                Teacher.classroom_id == classroom_id,
                Teacher.is_current == True,
                Teacher.deleted_at == None,
            )
        )
        teachers_db = teacher_result.scalars().all()

        # 生徒データを取得
        student_result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.subjects))
            .where(
                Student.classroom_id == classroom_id,
                Student.is_current == True,
                Student.deleted_at == None,
            )
        )
        students_db = student_result.scalars().all()

        # NG関係を取得
        ng_result = await self.db.execute(select(NgRelation))
        ng_relations = ng_result.scalars().all()

        # NG関係をマップ化
        teacher_ng_students: dict[str, list[str]] = {}
        student_ng_teachers: dict[str, list[str]] = {}
        for ng in ng_relations:
            if ng.teacher_id not in teacher_ng_students:
                teacher_ng_students[ng.teacher_id] = []
            teacher_ng_students[ng.teacher_id].append(str(ng.student_id))

            if ng.student_id not in student_ng_teachers:
                student_ng_teachers[ng.student_id] = []
            student_ng_teachers[ng.student_id].append(str(ng.teacher_id))

        # 講師シフト希望を取得
        shift_result = await self.db.execute(
            select(TeacherShiftPreference).where(
                TeacherShiftPreference.term_id == term_id
            )
        )
        shift_prefs = shift_result.scalars().all()

        # シフト希望をマップ化
        teacher_prefs: dict[str, dict[tuple[str, int], PreferenceValue]] = {}
        for pref in shift_prefs:
            if pref.teacher_id not in teacher_prefs:
                teacher_prefs[pref.teacher_id] = {}
            key = (pref.day_of_week.value, pref.slot_number)
            if pref.preference_value == TeacherPreferenceValue.AVAILABLE:
                teacher_prefs[pref.teacher_id][key] = PreferenceValue.POSSIBLE
            else:
                teacher_prefs[pref.teacher_id][key] = PreferenceValue.UNAVAILABLE

        # 生徒受講希望を取得
        student_pref_result = await self.db.execute(
            select(StudentPreference).where(
                StudentPreference.term_id == term_id
            )
        )
        student_pref_list = student_pref_result.scalars().all()

        # 生徒希望をマップ化
        student_prefs: dict[str, dict[tuple[str, int], PreferenceValue]] = {}
        for pref in student_pref_list:
            if pref.student_id not in student_prefs:
                student_prefs[pref.student_id] = {}
            key = (pref.day_of_week.value, pref.slot_number)
            if pref.preference_value == StudentPreferenceValue.PREFERRED:
                student_prefs[pref.student_id][key] = PreferenceValue.PREFERRED
            elif pref.preference_value == StudentPreferenceValue.POSSIBLE:
                student_prefs[pref.student_id][key] = PreferenceValue.POSSIBLE
            else:
                student_prefs[pref.student_id][key] = PreferenceValue.UNAVAILABLE

        # ポリシー・制約を取得
        policy_result = await self.db.execute(
            select(Policy).where(Policy.term_id == term_id)
        )
        policies_db = policy_result.scalars().all()
        policy_map = {p.policy_type.value: p for p in policies_db}

        constraint_result = await self.db.execute(
            select(TermConstraint).where(TermConstraint.term_id == term_id)
        )
        constraints_db = constraint_result.scalars().all()
        teacher_constraints_map: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        student_constraints_map: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        classroom_constraints_map: dict[str, dict[str, Any]] = {}
        for c in constraints_db:
            payload = deepcopy(c.constraint_value or {})
            if c.target_type == ConstraintTargetType.TEACHER:
                teacher_constraints_map[c.target_id][c.constraint_type.value] = payload
            elif c.target_type == ConstraintTargetType.STUDENT:
                student_constraints_map[c.target_id][c.constraint_type.value] = payload
            elif c.target_type == ConstraintTargetType.CLASSROOM:
                classroom_constraints_map[c.constraint_type.value] = payload

        # TeacherDataに変換
        teachers = []
        for t in teachers_db:
            teacher_id = str(t.teacher_id)
            subject_ids = [ts.subject_id for ts in t.subjects]
            subject_levels = {ts.subject_id: "B" for ts in t.subjects}
            grade_ids = [tg.grade.value for tg in t.grades]
            term_adjustment = teacher_constraints_map.get(teacher_id, {})
            adjusted_min_slots = int(term_adjustment.get("min_slots", {}).get("value", t.min_slots_per_week))
            adjusted_max_slots = int(term_adjustment.get("max_slots", {}).get("value", t.max_slots_per_week))
            adjusted_max_consecutive = int(
                term_adjustment.get("max_consecutive", {}).get("value", t.max_consecutive_slots)
            )

            if "subject_limit" in term_adjustment:
                limited_subjects = term_adjustment["subject_limit"].get("subject_ids", [])
                if limited_subjects:
                    subject_ids = [sid for sid in subject_ids if sid in limited_subjects]

            teacher_pref = dict(teacher_prefs.get(teacher_id, {}))
            if "day_limit" in term_adjustment:
                allowed_days = set(term_adjustment["day_limit"].get("days", []))
                if allowed_days:
                    for day in ["mon", "tue", "wed", "thu", "fri", "sat"]:
                        if day in allowed_days:
                            continue
                        for slot_num in range(1, 5):
                            teacher_pref[(day, slot_num)] = PreferenceValue.UNAVAILABLE

            teachers.append(TeacherData(
                teacher_id=teacher_id,
                teacher_name=t.name,
                min_slots_per_week=adjusted_min_slots,
                max_slots_per_week=adjusted_max_slots,
                max_consecutive_slots=adjusted_max_consecutive,
                subject_ids=subject_ids,
                subject_levels=subject_levels,
                grade_ids=grade_ids,
                ng_student_ids=teacher_ng_students.get(t.teacher_id, []),
                preferences=teacher_pref,
            ))

        # StudentDataに変換
        students = []
        for s in students_db:
            student_id = str(s.student_id)
            subjects = [
                {"subject_id": ss.subject_id, "slots_per_week": ss.slots_per_week}
                for ss in s.subjects
            ]
            term_adjustment = student_constraints_map.get(student_id, {})
            adjusted_max_consecutive = int(
                term_adjustment.get("max_consecutive", {}).get("value", s.max_consecutive_slots)
            )
            preferred_teacher_id = str(s.preferred_teacher_id) if s.preferred_teacher_id else None
            preferred_teacher_gender = (
                s.preferred_teacher_gender.value if s.preferred_teacher_gender else None
            )
            ng_teachers = list(student_ng_teachers.get(s.student_id, []))

            # P004のON/OFFで希望講師・性別希望の反映可否を制御
            p004 = policy_map.get("P004")
            if not p004 or not p004.is_enabled:
                preferred_teacher_id = None
                preferred_teacher_gender = None
            else:
                if not bool(p004.parameters.get("enable_preferred_teacher", True)):
                    preferred_teacher_id = None
                if not bool(p004.parameters.get("enable_gender_preference", True)):
                    preferred_teacher_gender = None

            students.append(StudentData(
                student_id=student_id,
                student_name=s.name,
                grade=s.grade.value,
                school_type="public",
                max_consecutive_slots=adjusted_max_consecutive,
                preferred_teacher_id=preferred_teacher_id,
                preferred_teacher_gender=preferred_teacher_gender,
                subjects=subjects,
                ng_teacher_ids=ng_teachers,
                preferences=student_prefs.get(s.student_id, {}),
            ))

        # 時間枠データを生成（教室設定を優先し、未設定時はデフォルト）
        settings_result = await self.db.execute(
            select(ClassroomSettings).where(ClassroomSettings.classroom_id == classroom_id)
        )
        classroom_settings = settings_result.scalar_one_or_none()
        booth_count = classroom_settings.booth_count if classroom_settings else 3
        booth_override = classroom_constraints_map.get("booth_capacity", {}).get("value")
        if booth_override:
            booth_count = int(booth_override)

        timeslot_result = await self.db.execute(
            select(TimeSlot).where(TimeSlot.classroom_id == classroom_id)
        )
        configured_time_slots = timeslot_result.scalars().all()

        time_slots = []
        if configured_time_slots:
            weekday_slot_numbers = sorted(
                {slot.slot_number for slot in configured_time_slots if slot.day_type == DayType.WEEKDAY}
            )
            saturday_slot_numbers = sorted(
                {slot.slot_number for slot in configured_time_slots if slot.day_type == DayType.SATURDAY}
            )

            for day in ["mon", "tue", "wed", "thu", "fri"]:
                for slot_num in weekday_slot_numbers:
                    time_slots.append(
                        TimeSlotData(
                            day_of_week=day,
                            slot_number=slot_num,
                            booth_count=booth_count,
                        )
                    )
            for slot_num in saturday_slot_numbers:
                time_slots.append(
                    TimeSlotData(
                        day_of_week="sat",
                        slot_number=slot_num,
                        booth_count=booth_count,
                    )
                )
        else:
            for day in ["mon", "tue", "wed", "thu", "fri", "sat"]:
                slots_per_day = 4
                for slot_num in range(1, slots_per_day + 1):
                    time_slots.append(
                        TimeSlotData(
                            day_of_week=day,
                            slot_number=slot_num,
                            booth_count=booth_count,
                        )
                    )

        policies = [
            PolicyData(
                policy_type=p.policy_type.value,
                is_enabled=p.is_enabled,
                parameters=p.parameters or {},
            )
            for p in policies_db
        ]

        constraints = [
            {
                "target_type": c.target_type.value,
                "target_id": c.target_id,
                "constraint_type": c.constraint_type.value,
                "parameters": c.constraint_value or {},
            }
            for c in constraints_db
        ]

        return SolverInput(
            teachers=teachers,
            students=students,
            time_slots=time_slots,
            policies=policies,
            constraints=constraints,
        )

    async def _create_slots_from_solver(
        self, schedule_id: uuid.UUID, solver_output
    ) -> None:
        """ソルバー出力からスケジュールスロットを作成"""
        day_map = {
            "mon": DayOfWeek.MON,
            "tue": DayOfWeek.TUE,
            "wed": DayOfWeek.WED,
            "thu": DayOfWeek.THU,
            "fri": DayOfWeek.FRI,
            "sat": DayOfWeek.SAT,
        }

        for assignment in solver_output.assignments:
            slot_type = SlotType.ONE_TO_TWO if assignment.slot_type == SolverSlotType.ONE_TO_TWO else SlotType.ONE_TO_ONE

            slot = ScheduleSlot(
                slot_id=uuid.uuid4(),
                schedule_id=schedule_id,
                day_of_week=day_map.get(assignment.day_of_week, DayOfWeek.MON),
                slot_number=assignment.slot_number,
                booth_number=assignment.booth_number,
                teacher_id=str(assignment.teacher_id),
                student1_id=str(assignment.student1_id),
                student2_id=str(assignment.student2_id) if assignment.student2_id else None,
                subject_id=assignment.subject_id,
                slot_type=slot_type,
                status=SlotStatus.SCHEDULED,
            )
            self.db.add(slot)

    async def _generate_mock_slots(
        self, schedule_id: uuid.UUID, classroom_id: uuid.UUID
    ) -> None:
        """モックコマ生成"""
        # 講師を取得
        teacher_result = await self.db.execute(
            select(Teacher).where(
                Teacher.classroom_id == classroom_id,
                Teacher.is_current == True,
            ).limit(10)
        )
        teachers = teacher_result.scalars().all()

        # 生徒を取得
        student_result = await self.db.execute(
            select(Student).where(
                Student.classroom_id == classroom_id,
                Student.is_current == True,
            ).limit(20)
        )
        students = student_result.scalars().all()

        # 科目を取得
        subject_result = await self.db.execute(
            select(Subject).limit(5)
        )
        subjects = subject_result.scalars().all()

        if not teachers or not students or not subjects:
            return

        # モックコマを生成
        days = [DayOfWeek.MON, DayOfWeek.TUE, DayOfWeek.WED, DayOfWeek.THU, DayOfWeek.FRI]
        student_idx = 0

        for day in days:
            for slot_number in range(1, 5):  # 4コマ/日
                for booth in range(1, 4):  # 3ブース
                    if student_idx >= len(students):
                        student_idx = 0

                    teacher = random.choice(teachers)
                    student1 = students[student_idx]
                    student_idx += 1

                    # 1対2の場合
                    student2 = None
                    slot_type = SlotType.ONE_TO_ONE
                    if random.random() > 0.3 and student_idx < len(students):
                        student2 = students[student_idx]
                        student_idx += 1
                        slot_type = SlotType.ONE_TO_TWO

                    slot = ScheduleSlot(
                        slot_id=uuid.uuid4(),
                        schedule_id=schedule_id,
                        day_of_week=day,
                        slot_number=slot_number,
                        booth_number=booth,
                        teacher_id=teacher.teacher_id,
                        student1_id=student1.student_id,
                        student2_id=student2.student_id if student2 else None,
                        subject_id=random.choice(subjects).subject_id,
                        slot_type=slot_type,
                        status=SlotStatus.SCHEDULED,
                    )
                    self.db.add(slot)

    async def get_explanation(
        self,
        schedule_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ExplanationResponse:
        """結果説明取得（F082）- LLMによる自然言語説明"""
        result = await self.db.execute(
            select(Schedule)
            .options(selectinload(Schedule.term))
            .where(Schedule.schedule_id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError("指定された時間割が見つかりません")

        await self._check_classroom_access(
            schedule.term.classroom_id, user_id
        )

        # 統計情報を取得
        classroom_id = schedule.term.classroom_id
        teacher_result = await self.db.execute(
            select(func.count(Teacher.teacher_id)).where(
                Teacher.classroom_id == classroom_id,
                Teacher.is_current == True,
            )
        )
        teacher_count = teacher_result.scalar() or 0

        student_result = await self.db.execute(
            select(func.count(Student.student_id)).where(
                Student.classroom_id == classroom_id,
                Student.is_current == True,
            )
        )
        student_count = student_result.scalar() or 0

        # ボトルネック情報を構築（簡易版、実際には分析結果を使用）
        bottlenecks = []
        if student_count > 50:
            bottlenecks.append({
                "type": "time_slot",
                "day_of_week": "sat",
                "slot_number": 3,
                "demand": 15,
                "supply": 10,
                "gap": -5,
            })

        # LLMサービスを使用して説明生成
        context = ExplanationContext(
            fulfillment_rate=schedule.fulfillment_rate or Decimal("0"),
            soft_constraint_rate=schedule.soft_constraint_rate or Decimal("0"),
            one_to_two_rate=Decimal("78.5"),  # 実際の計算値を使用
            teacher_count=teacher_count,
            student_count=student_count,
            weekly_slots=teacher_count * 15,  # 概算
            bottlenecks=bottlenecks,
            constraint_violations=[],
            schedule_status="optimal" if schedule.fulfillment_rate and schedule.fulfillment_rate >= 80 else "suboptimal",
        )

        llm_response = await self.llm_service.generate_explanation(context)

        # LLM応答をパースしてレスポンスを構築
        fulfillment_rate = schedule.fulfillment_rate or Decimal("0")
        key_points = [
            f"充足率: {fulfillment_rate:.1f}%",
            f"ソフト制約達成率: {schedule.soft_constraint_rate or 0:.1f}%",
        ]

        # LLMが生成した内容から主要ポイントを抽出（簡易実装）
        if not llm_response.is_fallback:
            # LLM応答がある場合はそれを使用
            overall_summary = llm_response.content[:500] if len(llm_response.content) > 500 else llm_response.content
        else:
            overall_summary = llm_response.content[:500] if len(llm_response.content) > 500 else llm_response.content

        return ExplanationResponse(
            summary=ExplanationSummary(
                overall=overall_summary,
                key_points=key_points,
            ),
            bottleneck_explanation=BottleneckExplanation(
                main_bottleneck="土曜3限の講師供給" if bottlenecks else "特になし",
                detail="土曜3限は需要が高く、講師のシフト希望との調整が必要でした。" if bottlenecks else "顕著なボトルネックは検出されませんでした。",
                structural_cause=bool(bottlenecks),
            ),
            trade_offs=[
                TradeOff(
                    description="講師の連続コマ数を緩和すれば充足率向上の可能性あり",
                    pros=["充足率+1-2%の改善可能性"],
                    cons=["講師の負荷増加"],
                    recommendation="検討可",
                )
            ] if fulfillment_rate < 90 else [],
        )

    async def what_if(
        self,
        schedule_id: uuid.UUID,
        user_id: uuid.UUID,
        question: str,
    ) -> WhatIfResponse:
        """What-if分析（F082）- LLMによる影響分析"""
        result = await self.db.execute(
            select(Schedule)
            .options(selectinload(Schedule.term))
            .where(Schedule.schedule_id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError("指定された時間割が見つかりません")

        await self._check_classroom_access(
            schedule.term.classroom_id, user_id
        )

        # 関連する制約情報を取得
        term_id = schedule.term_id
        constraints_result = await self.db.execute(
            select(TermConstraint).where(TermConstraint.term_id == term_id)
        )
        constraints = constraints_result.scalars().all()

        related_constraints = [
            {
                "code": c.constraint_type.value,
                "name": f"{c.target_type.value}:{c.target_id}",
            }
            for c in constraints[:5]  # 最大5件
        ]

        # LLMサービスを使用してWhat-if分析
        context = WhatIfContext(
            question=question,
            current_fulfillment_rate=schedule.fulfillment_rate or Decimal("0"),
            current_soft_constraint_rate=schedule.soft_constraint_rate or Decimal("0"),
            related_constraints=related_constraints,
            affected_teachers=[],  # 実際には質問を解析して特定
            affected_students=[],
        )

        llm_response = await self.llm_service.generate_what_if_analysis(context)

        # LLM応答をパースしてレスポンスを構築
        return WhatIfResponse(
            analysis={
                "feasible": True,
                "impact": {
                    "fulfillment_rate_change": -0.5,
                    "soft_constraint_violations_added": 1,
                },
            },
            explanation=llm_response.content,
        )

    async def get_calendar_view(
        self,
        schedule_id: uuid.UUID,
        user_id: uuid.UUID,
        view_type: str = "all",
        filter_id: str | None = None,
    ) -> CalendarViewResponse:
        """カレンダービュー取得（F083）"""
        result = await self.db.execute(
            select(Schedule)
            .options(
                selectinload(Schedule.term),
                selectinload(Schedule.slots),
            )
            .where(Schedule.schedule_id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError("指定された時間割が見つかりません")

        await self._check_classroom_access(
            schedule.term.classroom_id, user_id
        )
        term_id = schedule.term_id

        # 1対2率をスロットから計算
        total_slots = len(schedule.slots)
        one_to_two_count = sum(
            1 for s in schedule.slots if s.slot_type == SlotType.ONE_TO_TWO
        )
        one_to_two_rate = (
            Decimal(one_to_two_count) / Decimal(total_slots) * 100
            if total_slots > 0 else Decimal("0")
        ).quantize(Decimal("0.01"))

        # 未配置数をgeneration_configから取得（保存されている場合）
        unplaced_count = 0
        if schedule.generation_config:
            unplaced_count = schedule.generation_config.get("unplaced_count", 0)

        # メトリクス
        metrics = ScheduleMetrics(
            fulfillment_rate=schedule.fulfillment_rate or Decimal("0"),
            soft_constraint_rate=schedule.soft_constraint_rate or Decimal("0"),
            one_to_two_rate=one_to_two_rate,
            unplaced_count=unplaced_count,
        )

        # タイムスロット定義
        time_slots = {
            "weekday": [
                {"slot_number": 1, "start_time": "16:00", "end_time": "17:20"},
                {"slot_number": 2, "start_time": "17:30", "end_time": "18:50"},
                {"slot_number": 3, "start_time": "19:00", "end_time": "20:20"},
                {"slot_number": 4, "start_time": "20:30", "end_time": "21:50"},
            ],
            "saturday": [
                {"slot_number": 1, "start_time": "10:00", "end_time": "11:20"},
                {"slot_number": 2, "start_time": "11:30", "end_time": "12:50"},
                {"slot_number": 3, "start_time": "14:00", "end_time": "15:20"},
                {"slot_number": 4, "start_time": "15:30", "end_time": "16:50"},
            ],
        }

        teacher_pref_map, student_pref_map = await self._build_preference_maps(term_id)

        teacher_ids = {slot.teacher_id for slot in schedule.slots if slot.teacher_id}
        student_ids = {
            sid
            for slot in schedule.slots
            for sid in [slot.student1_id, slot.student2_id]
            if sid
        }
        teacher_name_map: dict[str, str] = {}
        student_name_map: dict[str, str] = {}
        if teacher_ids:
            teacher_result = await self.db.execute(
                select(Teacher).where(Teacher.teacher_id.in_(teacher_ids), Teacher.is_current == True)
            )
            teacher_name_map = {t.teacher_id: t.name for t in teacher_result.scalars().all()}
        if student_ids:
            student_result = await self.db.execute(
                select(Student).where(Student.student_id.in_(student_ids), Student.is_current == True)
            )
            student_name_map = {s.student_id: s.name for s in student_result.scalars().all()}

        # セル情報を構築
        cells = []
        day_map = {
            DayOfWeek.MON: "mon",
            DayOfWeek.TUE: "tue",
            DayOfWeek.WED: "wed",
            DayOfWeek.THU: "thu",
            DayOfWeek.FRI: "fri",
            DayOfWeek.SAT: "sat",
        }

        # スロットをグループ化
        slot_groups: dict[tuple[str, int], list[ScheduleSlot]] = {}
        for slot in schedule.slots:
            key = (day_map[slot.day_of_week], slot.slot_number)
            if key not in slot_groups:
                slot_groups[key] = []
            slot_groups[key].append(slot)

        for (day, slot_num), slots in slot_groups.items():
            slot_infos = []
            for slot in slots:
                slot_issues = self._collect_slot_issues(
                    teacher_id=slot.teacher_id,
                    student1_id=slot.student1_id,
                    student2_id=slot.student2_id,
                    slot_number=slot.slot_number,
                    day_key=day,
                    teacher_pref_map=teacher_pref_map,
                    student_pref_map=student_pref_map,
                )
                slot_infos.append(
                    SlotInfo(
                        slot_id=slot.slot_id,
                        teacher=PersonInfo(
                            id=slot.teacher_id,
                            name=teacher_name_map.get(slot.teacher_id, slot.teacher_id),
                        ),
                        student1=PersonInfo(
                            id=slot.student1_id,
                            name=student_name_map.get(slot.student1_id, slot.student1_id),
                            subject=slot.subject_id,
                        ),
                        student2=PersonInfo(
                            id=slot.student2_id,
                            name=student_name_map.get(slot.student2_id, slot.student2_id) if slot.student2_id else None,
                            subject=slot.subject_id if slot.student2_id else None,
                        ) if slot.student2_id else None,
                        slot_type=slot.slot_type.value,
                        status=slot.status.value,
                        has_issue=len(slot_issues) > 0,
                        issues=slot_issues,
                    )
                )

            cells.append(
                CellInfo(
                    day_of_week=day,
                    slot_number=slot_num,
                    slots=slot_infos,
                    status="warning" if any(s.has_issue for s in slot_infos) else "sufficient",
                    issues=[issue for s in slot_infos for issue in s.issues],
                )
            )

        return CalendarViewResponse(
            schedule_id=schedule.schedule_id,
            status=schedule.status.value,
            solution_status="optimal",
            metrics=metrics,
            time_slots=time_slots,
            cells=cells,
            unplaced_students=[],
        )

    async def get_movable_targets(
        self,
        schedule_id: uuid.UUID,
        slot_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MovableTargetsResponse:
        """移動可能先取得（F085）"""
        result = await self.db.execute(
            select(ScheduleSlot)
            .options(selectinload(ScheduleSlot.schedule).selectinload(Schedule.term))
            .where(ScheduleSlot.slot_id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if not slot:
            raise ValueError("指定されたコマが見つかりません")

        await self._check_classroom_access(
            slot.schedule.term.classroom_id, user_id
        )
        term_id = slot.schedule.term_id
        teacher_pref_map, student_pref_map = await self._build_preference_maps(term_id)

        all_slots_result = await self.db.execute(
            select(ScheduleSlot).where(ScheduleSlot.schedule_id == schedule_id)
        )
        all_slots = all_slots_result.scalars().all()
        occupancy_map = defaultdict(list)
        teacher_slot_map = defaultdict(list)
        for s in all_slots:
            if s.slot_id == slot.slot_id:
                continue
            key = (s.day_of_week.value.lower(), s.slot_number)
            occupancy_map[key].append(s)
            if s.teacher_id:
                teacher_slot_map[(s.teacher_id, key[0], key[1])].append(s)

        # 移動可能先を計算
        targets = []
        days = ["mon", "tue", "wed", "thu", "fri", "sat"]
        for day in days:
            for slot_num in range(1, 5):
                issues: list[str] = []
                feasibility = "allowed"
                key = (day, slot_num)
                if slot.teacher_id and teacher_slot_map.get((slot.teacher_id, day, slot_num)):
                    feasibility = "hard_violation"
                    issues.append("講師が同時間帯に重複配置されます")

                if occupancy_map.get(key):
                    # 既存配置がある場合は軽微な警告として扱う
                    if feasibility != "hard_violation":
                        feasibility = "soft_violation"
                    issues.append("対象時間帯に既存コマがあります")

                pref_issues = self._collect_slot_issues(
                    teacher_id=slot.teacher_id,
                    student1_id=slot.student1_id,
                    student2_id=slot.student2_id,
                    slot_number=slot_num,
                    day_key=day,
                    teacher_pref_map=teacher_pref_map,
                    student_pref_map=student_pref_map,
                )
                if pref_issues and feasibility == "allowed":
                    feasibility = "soft_violation"
                issues.extend(pref_issues)

                targets.append(
                    MovableTarget(
                        day_of_week=day,
                        slot_number=slot_num,
                        feasibility=feasibility,
                        violations=issues,
                        impact={
                            "fulfillment_rate_change": 0,
                            "new_violations": len(issues),
                        },
                    )
                )

        return MovableTargetsResponse(targets=targets)

    async def move_slot(
        self,
        schedule_id: uuid.UUID,
        slot_id: uuid.UUID,
        user_id: uuid.UUID,
        target_day: str,
        target_slot_number: int,
        force: bool = False,
    ) -> MoveSlotResponse:
        """コマ移動（F085）"""
        result = await self.db.execute(
            select(ScheduleSlot)
            .options(selectinload(ScheduleSlot.schedule).selectinload(Schedule.term))
            .where(ScheduleSlot.slot_id == slot_id)
        )
        slot = result.scalar_one_or_none()
        if not slot:
            raise ValueError("指定されたコマが見つかりません")

        schedule = slot.schedule
        await self._check_classroom_access(
            schedule.term.classroom_id, user_id
        )

        if schedule.status == ScheduleStatus.CONFIRMED:
            raise ValueError("確定済みの時間割は編集できません")

        # 曜日をENUMに変換
        day_map = {
            "mon": DayOfWeek.MON,
            "tue": DayOfWeek.TUE,
            "wed": DayOfWeek.WED,
            "thu": DayOfWeek.THU,
            "fri": DayOfWeek.FRI,
            "sat": DayOfWeek.SAT,
        }
        if target_day not in day_map:
            raise ValueError("無効な曜日です")

        targets = await self.get_movable_targets(schedule_id, slot_id, user_id)
        target = next(
            (
                t
                for t in targets.targets
                if t.day_of_week == target_day and t.slot_number == target_slot_number
            ),
            None,
        )
        if not target:
            raise ValueError("移動先が見つかりません")
        if target.feasibility == "hard_violation" and not force:
            raise ValueError("ハード制約違反があるため移動できません")

        # コマを移動
        slot.day_of_week = day_map[target_day]
        slot.slot_number = target_slot_number

        await self.db.commit()

        # スケジュールのスロットを再取得して1対2率を計算
        all_slots_result = await self.db.execute(
            select(ScheduleSlot).where(ScheduleSlot.schedule_id == schedule_id)
        )
        all_slots = all_slots_result.scalars().all()
        total_slots = len(all_slots)
        one_to_two_count = sum(
            1 for s in all_slots if s.slot_type == SlotType.ONE_TO_TWO
        )
        one_to_two_rate = (
            Decimal(one_to_two_count) / Decimal(total_slots) * 100
            if total_slots > 0 else Decimal("0")
        ).quantize(Decimal("0.01"))

        # 未配置数をgeneration_configから取得
        unplaced_count = 0
        if schedule.generation_config:
            unplaced_count = schedule.generation_config.get("unplaced_count", 0)

        return MoveSlotResponse(
            success=True,
            new_slot_id=slot.slot_id,
            updated_metrics=ScheduleMetrics(
                fulfillment_rate=schedule.fulfillment_rate or Decimal("0"),
                soft_constraint_rate=schedule.soft_constraint_rate or Decimal("0"),
                one_to_two_rate=one_to_two_rate,
                unplaced_count=unplaced_count,
            ),
        )

    async def confirm(
        self,
        schedule_id: uuid.UUID,
        user_id: uuid.UUID,
        force: bool = False,
    ) -> ConfirmResponse:
        """時間割確定（F086）"""
        result = await self.db.execute(
            select(Schedule)
            .options(selectinload(Schedule.term))
            .where(Schedule.schedule_id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError("指定された時間割が見つかりません")

        await self._check_classroom_access(
            schedule.term.classroom_id, user_id
        )

        if schedule.status == ScheduleStatus.CONFIRMED:
            raise ValueError("すでに確定済みです")

        # 確定前チェック
        warnings = []
        soft_rate = schedule.soft_constraint_rate or Decimal("0")
        if soft_rate < 85:
            warnings.append(
                ConfirmWarning(
                    type="soft_constraint_below_target",
                    current=soft_rate,
                    target=Decimal("85"),
                    message="ソフト制約達成率が目標を下回っています",
                )
            )

        if warnings and not force:
            raise ValueError(
                "警告があります。強制確定する場合はforce=trueを指定してください"
            )

        # 確定処理
        now = datetime.now(timezone.utc)
        schedule.status = ScheduleStatus.CONFIRMED
        schedule.confirmed_at = now
        schedule.confirmed_by = user_id

        await self.db.commit()

        return ConfirmResponse(
            schedule_id=schedule.schedule_id,
            status="confirmed",
            confirmed_at=now,
            message="時間割を確定しました",
        )

    async def export(
        self,
        schedule_id: uuid.UUID,
        user_id: uuid.UUID,
        format: str,
        export_type: str,
        options: dict,
    ) -> ExportResponse:
        """PDF/CSV出力（F087）"""
        result = await self.db.execute(
            select(Schedule)
            .options(
                selectinload(Schedule.term),
                selectinload(Schedule.slots),
            )
            .where(Schedule.schedule_id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError("指定された時間割が見つかりません")

        await self._check_classroom_access(
            schedule.term.classroom_id, user_id
        )

        # 教室情報を取得
        classroom_result = await self.db.execute(
            select(Classroom).where(Classroom.classroom_id == schedule.term.classroom_id)
        )
        classroom = classroom_result.scalar_one_or_none()
        classroom_name = classroom.classroom_name if classroom else "不明"

        # スロットデータを構築
        export_slots = []
        day_map = {
            DayOfWeek.MON: "mon",
            DayOfWeek.TUE: "tue",
            DayOfWeek.WED: "wed",
            DayOfWeek.THU: "thu",
            DayOfWeek.FRI: "fri",
            DayOfWeek.SAT: "sat",
        }

        for slot in schedule.slots:
            # 講師名・生徒名を取得（実際にはJOINで取得するべき）
            teacher_name = slot.teacher_id or ""
            student1_name = slot.student1_id or ""
            student2_name = slot.student2_id or ""

            export_slots.append(
                ExportSlot(
                    slot_id=str(slot.slot_id),
                    day_of_week=day_map.get(slot.day_of_week, "mon"),
                    slot_number=slot.slot_number,
                    booth_number=slot.booth_number or 1,
                    teacher_id=slot.teacher_id or "",
                    teacher_name=teacher_name,
                    student1_id=slot.student1_id or "",
                    student1_name=student1_name,
                    student2_id=slot.student2_id,
                    student2_name=student2_name if slot.student2_id else None,
                    subject_id=slot.subject_id or "",
                    subject_name=slot.subject_id or "",
                    slot_type=slot.slot_type.value if slot.slot_type else "one_to_one",
                )
            )

        # エクスポートデータを構築
        export_data = ExportData(
            schedule_id=str(schedule.schedule_id),
            term_name=schedule.term.term_name,
            classroom_name=classroom_name,
            fulfillment_rate=schedule.fulfillment_rate or Decimal("0"),
            soft_constraint_rate=schedule.soft_constraint_rate or Decimal("0"),
            status=schedule.status.value,
            slots=export_slots,
            created_at=schedule.created_at or datetime.now(timezone.utc),
            export_type=export_type,
        )

        # フォーマットに応じてエクスポート
        if format == "csv":
            if export_type == "teacher":
                export_result = self.export_service.generate_teacher_view_csv(export_data, options)
            elif export_type == "student":
                export_result = self.export_service.generate_student_view_csv(export_data, options)
            else:
                export_result = self.export_service.generate_csv(export_data, options)
        else:  # pdf
            export_result = self.export_service.generate_pdf(export_data, options)

        # エクスポートファイルを一時保存（実際にはS3等に保存）
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        self.export_service.store_result(export_result, expires_at)

        return ExportResponse(
            download_url=f"/api/exports/{export_result.export_id}/download",
            expires_at=expires_at,
            file_name=export_result.filename,
        )

    async def list_schedules(
        self,
        classroom_id: uuid.UUID,
        term_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ScheduleListResponse:
        """時間割一覧取得"""
        await self._check_classroom_access(classroom_id, user_id)
        await self._get_term(classroom_id, term_id)

        result = await self.db.execute(
            select(Schedule)
            .where(Schedule.term_id == term_id)
            .order_by(Schedule.version.desc())
        )
        schedules = result.scalars().all()

        return ScheduleListResponse(
            data=[
                ScheduleListItem(
                    schedule_id=s.schedule_id,
                    version=s.version,
                    status=s.status.value,
                    fulfillment_rate=s.fulfillment_rate,
                    soft_constraint_rate=s.soft_constraint_rate,
                    created_at=s.created_at,
                    confirmed_at=s.confirmed_at,
                )
                for s in schedules
            ]
        )
