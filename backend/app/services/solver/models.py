"""
ソルバー入出力モデル定義
"""
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


class SlotType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_TWO = "one_to_two"


class PreferenceValue(str, Enum):
    PREFERRED = "preferred"
    POSSIBLE = "possible"
    UNAVAILABLE = "unavailable"


@dataclass
class TeacherData:
    """講師データ"""
    teacher_id: UUID
    teacher_name: str
    min_slots_per_week: int
    max_slots_per_week: int
    max_consecutive_slots: int
    subject_ids: list[str]  # 担当可能科目
    subject_levels: dict[str, str]  # 科目ID -> レベル(A/B/C)
    grade_ids: list[str]  # 担当可能学年
    ng_student_ids: list[UUID]  # NG生徒
    preferences: dict[tuple[str, int], PreferenceValue]  # (曜日, コマ) -> 希望


@dataclass
class StudentData:
    """生徒データ"""
    student_id: UUID
    student_name: str
    grade: str
    school_type: str  # public/private
    max_consecutive_slots: int
    preferred_teacher_id: UUID | None
    preferred_teacher_gender: str | None  # male/female/none
    subjects: list[dict]  # [{subject_id, slots_per_week}]
    ng_teacher_ids: list[UUID]
    preferences: dict[tuple[str, int], PreferenceValue]  # (曜日, コマ) -> 希望


@dataclass
class TimeSlotData:
    """時間枠データ"""
    day_of_week: str
    slot_number: int
    booth_count: int


@dataclass
class PolicyData:
    """ポリシーデータ"""
    policy_type: str
    is_enabled: bool
    parameters: dict[str, Any]


@dataclass
class SolverInput:
    """ソルバー入力"""
    teachers: list[TeacherData]
    students: list[StudentData]
    time_slots: list[TimeSlotData]
    policies: list[PolicyData]
    constraints: list[dict]  # ターム固有制約


@dataclass
class SolverConfig:
    """ソルバー設定"""
    max_timeout_seconds: int = 60
    strategy: str = "standard"  # standard/relaxed/partial
    enable_soft_constraints: bool = True


@dataclass
class SlotAssignment:
    """コマ割り当て結果"""
    day_of_week: str
    slot_number: int
    booth_number: int
    teacher_id: UUID
    student1_id: UUID
    student2_id: UUID | None
    subject_id: str
    slot_type: SlotType


@dataclass
class UnplacedStudent:
    """未配置生徒"""
    student_id: UUID
    student_name: str
    subject_id: str
    reason: str


@dataclass
class ConstraintViolation:
    """制約違反"""
    constraint_type: str
    severity: str  # hard/soft
    description: str
    affected_entities: list[str]


@dataclass
class SolverStats:
    """ソルバー統計"""
    solve_time_ms: int
    solutions_found: int
    optimality_gap: Decimal
    strategy_used: str
    termination_reason: str


@dataclass
class SolverOutput:
    """ソルバー出力"""
    status: str  # optimal/feasible/partial/infeasible
    assignments: list[SlotAssignment] = field(default_factory=list)
    unplaced_students: list[UnplacedStudent] = field(default_factory=list)
    violations: list[ConstraintViolation] = field(default_factory=list)
    soft_constraint_rate: Decimal = Decimal("0")
    one_to_two_rate: Decimal = Decimal("0")
    stats: SolverStats | None = None
