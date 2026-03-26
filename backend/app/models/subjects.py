"""科目関連モデル"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import GradeCategory, NgCreatedBy, SubjectCategory


class Subject(Base):
    """科目マスタテーブル"""
    __tablename__ = "subjects"

    subject_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )
    subject_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    grade_category: Mapped[GradeCategory] = mapped_column(
        Enum(GradeCategory, name="grade_category", create_type=True),
        nullable=False,
    )
    subject_category: Mapped[SubjectCategory] = mapped_column(
        Enum(SubjectCategory, name="subject_category", create_type=True),
        nullable=False,
    )
    is_jhs_exam_target: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    is_hs_exam_target: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    # Relationships
    teacher_subjects: Mapped[list["TeacherSubject"]] = relationship(
        "TeacherSubject",
        back_populates="subject",
    )
    student_subjects: Mapped[list["StudentSubject"]] = relationship(
        "StudentSubject",
        back_populates="subject",
    )
    schedule_slots: Mapped[list["ScheduleSlot"]] = relationship(
        "ScheduleSlot",
        back_populates="subject",
    )


class NgRelation(Base):
    """NG関係テーブル"""
    __tablename__ = "ng_relations"
    __table_args__ = (
        UniqueConstraint("teacher_id", "student_id", name="uq_ng_relations"),
    )

    ng_relation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    teacher_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    student_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    created_by: Mapped[NgCreatedBy] = mapped_column(
        Enum(NgCreatedBy, name="ng_created_by", create_type=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
