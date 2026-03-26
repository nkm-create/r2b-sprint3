"""時間割関連モデル"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin
from app.models.enums import (
    AbsentType,
    ConstraintTargetType,
    ConstraintType,
    DayOfWeek,
    PolicyType,
    ScheduleStatus,
    SlotStatus,
    SlotType,
    SubstitutionStatus,
    SubstitutionType,
    TermStatus,
)


class Term(Base, TimestampMixin, SoftDeleteMixin):
    """タームテーブル"""
    __tablename__ = "terms"

    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        nullable=False,
        index=True,
    )
    term_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    status: Mapped[TermStatus] = mapped_column(
        Enum(TermStatus, name="term_status", create_type=True),
        nullable=False,
        default=TermStatus.CREATING,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="terms")
    constraints: Mapped[list["TermConstraint"]] = relationship(
        "TermConstraint",
        back_populates="term",
        cascade="all, delete-orphan",
    )
    policies: Mapped[list["Policy"]] = relationship(
        "Policy",
        back_populates="term",
        cascade="all, delete-orphan",
    )
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule",
        back_populates="term",
    )
    teacher_shift_preferences: Mapped[list["TeacherShiftPreference"]] = relationship(
        "TeacherShiftPreference",
        back_populates="term",
    )
    student_preferences: Mapped[list["StudentPreference"]] = relationship(
        "StudentPreference",
        back_populates="term",
    )


class TermConstraint(Base, TimestampMixin):
    """ターム固有制約テーブル"""
    __tablename__ = "term_constraints"

    constraint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.term_id"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[ConstraintTargetType] = mapped_column(
        Enum(ConstraintTargetType, name="constraint_target_type", create_type=True),
        nullable=False,
    )
    target_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    constraint_type: Mapped[ConstraintType] = mapped_column(
        Enum(ConstraintType, name="constraint_type", create_type=True),
        nullable=False,
    )
    constraint_value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Relationships
    term: Mapped["Term"] = relationship("Term", back_populates="constraints")


class Policy(Base, TimestampMixin):
    """全体ポリシー設定テーブル"""
    __tablename__ = "policies"
    __table_args__ = (
        UniqueConstraint("term_id", "policy_type", name="uq_policies"),
    )

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.term_id"),
        nullable=False,
    )
    policy_type: Mapped[PolicyType] = mapped_column(
        Enum(PolicyType, name="policy_type", create_type=True),
        nullable=False,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    parameters: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Relationships
    term: Mapped["Term"] = relationship("Term", back_populates="policies")


class PolicyTemplate(Base, TimestampMixin):
    """ポリシーテンプレートテーブル"""
    __tablename__ = "policy_templates"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        nullable=False,
    )
    template_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    policies: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="policy_templates")


class Schedule(Base, TimestampMixin):
    """時間割テーブル（バージョン管理）"""
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint(
            "fulfillment_rate IS NULL OR (fulfillment_rate >= 0 AND fulfillment_rate <= 100)",
            name="chk_schedules_fulfillment",
        ),
    )

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.term_id"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus, name="schedule_status", create_type=True),
        nullable=False,
        default=ScheduleStatus.DRAFT,
    )
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedules.schedule_id"),
        nullable=True,
    )
    master_snapshot: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    generation_config: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    fulfillment_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    soft_constraint_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    # Relationships
    term: Mapped["Term"] = relationship("Term", back_populates="schedules")
    parent_version: Mapped["Schedule | None"] = relationship(
        "Schedule",
        remote_side=[schedule_id],
        foreign_keys=[parent_version_id],
    )
    slots: Mapped[list["ScheduleSlot"]] = relationship(
        "ScheduleSlot",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )
    confirmer: Mapped["User | None"] = relationship("User")


class ScheduleSlot(Base, TimestampMixin):
    """時間割コマテーブル"""
    __tablename__ = "schedule_slots"

    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedules.schedule_id"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Enum(DayOfWeek, name="day_of_week", create_type=True),
        nullable=False,
    )
    slot_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    booth_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    teacher_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    student1_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    student2_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    subject_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("subjects.subject_id"),
        nullable=False,
    )
    slot_type: Mapped[SlotType] = mapped_column(
        Enum(SlotType, name="slot_type", create_type=True),
        nullable=False,
    )
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus, name="slot_status", create_type=True),
        nullable=False,
        default=SlotStatus.SCHEDULED,
    )

    # Relationships
    schedule: Mapped["Schedule"] = relationship("Schedule", back_populates="slots")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="schedule_slots")
    absences: Mapped[list["Absence"]] = relationship(
        "Absence",
        back_populates="slot",
    )


class Absence(Base, TimestampMixin):
    """欠席記録テーブル"""
    __tablename__ = "absences"

    absence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedule_slots.slot_id"),
        nullable=False,
        index=True,
    )
    absent_type: Mapped[AbsentType] = mapped_column(
        Enum(AbsentType, name="absent_type", create_type=True),
        nullable=False,
    )
    absent_person_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    absence_reason: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    needs_substitution: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    substitution_status: Mapped[SubstitutionStatus] = mapped_column(
        Enum(SubstitutionStatus, name="substitution_status", create_type=True),
        nullable=False,
        default=SubstitutionStatus.PENDING,
    )
    registered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )

    # Relationships
    slot: Mapped["ScheduleSlot"] = relationship("ScheduleSlot", back_populates="absences")
    registerer: Mapped["User"] = relationship("User")
    substitution: Mapped["Substitution | None"] = relationship(
        "Substitution",
        back_populates="absence",
        uselist=False,
    )


class Substitution(Base):
    """振替記録テーブル"""
    __tablename__ = "substitutions"

    substitution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    absence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("absences.absence_id"),
        nullable=False,
    )
    original_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedule_slots.slot_id"),
        nullable=False,
    )
    new_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedule_slots.slot_id"),
        nullable=False,
    )
    substitution_type: Mapped[SubstitutionType] = mapped_column(
        Enum(SubstitutionType, name="substitution_type", create_type=True),
        nullable=False,
    )
    priority_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    confirmed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    absence: Mapped["Absence"] = relationship("Absence", back_populates="substitution")
    original_slot: Mapped["ScheduleSlot"] = relationship(
        "ScheduleSlot",
        foreign_keys=[original_slot_id],
    )
    new_slot: Mapped["ScheduleSlot"] = relationship(
        "ScheduleSlot",
        foreign_keys=[new_slot_id],
    )
    confirmer: Mapped["User"] = relationship("User")
