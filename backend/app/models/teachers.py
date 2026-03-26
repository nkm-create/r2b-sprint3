"""講師関連モデル"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin
from app.models.enums import (
    Gender,
    Grade,
    TeacherChangeReason,
    TeacherStatus,
    UniversityRank,
)


class Teacher(Base, TimestampMixin, SoftDeleteMixin):
    """講師テーブル（バージョン管理）"""
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("teacher_id", "classroom_id", "version_number", name="uq_teachers_version"),
        CheckConstraint("min_slots_per_week <= max_slots_per_week", name="chk_teachers_slots"),
        CheckConstraint("max_consecutive_slots BETWEEN 1 AND 4", name="chk_teachers_consecutive"),
    )

    teacher_version_id: Mapped[uuid.UUID] = mapped_column(
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
        index=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    change_reason_type: Mapped[TeacherChangeReason] = mapped_column(
        Enum(TeacherChangeReason, name="teacher_change_reason", create_type=True),
        nullable=False,
    )
    change_reason_note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, name="gender", create_type=True),
        nullable=False,
    )
    min_slots_per_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    max_slots_per_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    max_consecutive_slots: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    has_jhs_exam_experience: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    has_hs_exam_experience: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    university_rank: Mapped[UniversityRank | None] = mapped_column(
        Enum(UniversityRank, name="university_rank", create_type=True),
        nullable=True,
    )
    status: Mapped[TeacherStatus] = mapped_column(
        Enum(TeacherStatus, name="teacher_status", create_type=True),
        nullable=False,
        default=TeacherStatus.ACTIVE,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="teachers")
    subjects: Mapped[list["TeacherSubject"]] = relationship(
        "TeacherSubject",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    grades: Mapped[list["TeacherGrade"]] = relationship(
        "TeacherGrade",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    shift_preferences: Mapped[list["TeacherShiftPreference"]] = relationship(
        "TeacherShiftPreference",
        back_populates="teacher",
        foreign_keys="TeacherShiftPreference.teacher_id",
        primaryjoin="Teacher.teacher_id == foreign(TeacherShiftPreference.teacher_id)",
    )


class TeacherSubject(Base):
    """講師-指導可能科目中間テーブル"""
    __tablename__ = "teacher_subjects"

    teacher_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.teacher_version_id"),
        primary_key=True,
    )
    subject_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("subjects.subject_id"),
        primary_key=True,
    )

    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="subjects")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="teacher_subjects")


class TeacherGrade(Base):
    """講師-指導可能学年中間テーブル"""
    __tablename__ = "teacher_grades"

    teacher_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.teacher_version_id"),
        primary_key=True,
    )
    grade: Mapped[Grade] = mapped_column(
        Enum(Grade, name="grade", create_type=True),
        primary_key=True,
    )

    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="grades")
