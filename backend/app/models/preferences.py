"""希望データ関連モデル"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import DayOfWeek, StudentPreferenceValue, TeacherPreferenceValue


class TeacherShiftPreference(Base, TimestampMixin):
    """講師シフト希望テーブル"""
    __tablename__ = "teacher_shift_preferences"
    __table_args__ = (
        UniqueConstraint("teacher_id", "term_id", "day_of_week", "slot_number", name="uq_teacher_shift_prefs"),
    )

    preference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    teacher_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        nullable=False,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.term_id"),
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
    preference_value: Mapped[TeacherPreferenceValue] = mapped_column(
        Enum(TeacherPreferenceValue, name="teacher_preference_value", create_type=True),
        nullable=False,
    )
    is_manually_edited: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom")
    term: Mapped["Term"] = relationship("Term", back_populates="teacher_shift_preferences")
    teacher: Mapped["Teacher"] = relationship(
        "Teacher",
        back_populates="shift_preferences",
        foreign_keys=[teacher_id],
        primaryjoin="TeacherShiftPreference.teacher_id == Teacher.teacher_id",
    )


class StudentPreference(Base, TimestampMixin):
    """生徒受講希望テーブル"""
    __tablename__ = "student_preferences"
    __table_args__ = (
        UniqueConstraint("student_id", "term_id", "day_of_week", "slot_number", name="uq_student_prefs"),
    )

    preference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    student_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        nullable=False,
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("terms.term_id"),
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
    preference_value: Mapped[StudentPreferenceValue] = mapped_column(
        Enum(StudentPreferenceValue, name="student_preference_value", create_type=True),
        nullable=False,
    )
    is_manually_edited: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom")
    term: Mapped["Term"] = relationship("Term", back_populates="student_preferences")
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="preferences",
        foreign_keys=[student_id],
        primaryjoin="StudentPreference.student_id == Student.student_id",
    )
