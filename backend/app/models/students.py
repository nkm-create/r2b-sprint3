"""生徒関連モデル"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin
from app.models.enums import (
    AspirationLevel,
    EnrollmentPurpose,
    Grade,
    PreferredGender,
    StudentChangeReason,
    StudentStatus,
)


class Student(Base, TimestampMixin, SoftDeleteMixin):
    """生徒テーブル（バージョン管理）"""
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("student_id", "classroom_id", "version_number", name="uq_students_version"),
        CheckConstraint("max_consecutive_slots BETWEEN 1 AND 4", name="chk_students_consecutive"),
    )

    student_version_id: Mapped[uuid.UUID] = mapped_column(
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
    change_reason_type: Mapped[StudentChangeReason] = mapped_column(
        Enum(StudentChangeReason, name="student_change_reason", create_type=True),
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
    grade: Mapped[Grade] = mapped_column(
        Enum(Grade, name="grade", create_type=True),
        nullable=False,
    )
    max_consecutive_slots: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    preferred_teacher_id: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    preferred_teacher_gender: Mapped[PreferredGender | None] = mapped_column(
        Enum(PreferredGender, name="preferred_gender", create_type=True),
        nullable=True,
    )
    aspiration_level: Mapped[AspirationLevel | None] = mapped_column(
        Enum(AspirationLevel, name="aspiration_level", create_type=True),
        nullable=True,
    )
    enrollment_purpose: Mapped[EnrollmentPurpose | None] = mapped_column(
        Enum(EnrollmentPurpose, name="enrollment_purpose", create_type=True),
        nullable=True,
    )
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus, name="student_status", create_type=True),
        nullable=False,
        default=StudentStatus.ACTIVE,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="students")
    subjects: Mapped[list["StudentSubject"]] = relationship(
        "StudentSubject",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    preferences: Mapped[list["StudentPreference"]] = relationship(
        "StudentPreference",
        back_populates="student",
        foreign_keys="StudentPreference.student_id",
        primaryjoin="Student.student_id == foreign(StudentPreference.student_id)",
    )


class StudentSubject(Base):
    """生徒-科目別コマ数中間テーブル"""
    __tablename__ = "student_subjects"
    __table_args__ = (
        CheckConstraint("slots_per_week >= 1", name="chk_student_subjects_slots"),
    )

    student_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.student_version_id"),
        primary_key=True,
    )
    subject_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("subjects.subject_id"),
        primary_key=True,
    )
    slots_per_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="subjects")
    subject: Mapped["Subject"] = relationship("Subject", back_populates="student_subjects")
