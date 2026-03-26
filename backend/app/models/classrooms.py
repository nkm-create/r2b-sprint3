"""教室関連モデル"""
import uuid
from datetime import datetime, time

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin
from app.models.enums import ClassroomStatus, DayType, GoogleFormDataType


class Area(Base, TimestampMixin):
    """エリアテーブル"""
    __tablename__ = "areas"

    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    area_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Relationships
    classrooms: Mapped[list["Classroom"]] = relationship(
        "Classroom",
        back_populates="area",
    )
    user_areas: Mapped[list["UserArea"]] = relationship(
        "UserArea",
        back_populates="area",
    )


class Classroom(Base, TimestampMixin, SoftDeleteMixin):
    """教室テーブル"""
    __tablename__ = "classrooms"

    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("areas.area_id"),
        nullable=False,
        index=True,
    )
    classroom_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    classroom_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    address: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    status: Mapped[ClassroomStatus] = mapped_column(
        Enum(ClassroomStatus, name="classroom_status", create_type=True),
        nullable=False,
        default=ClassroomStatus.OPERATING,
    )

    # Relationships
    area: Mapped["Area"] = relationship("Area", back_populates="classrooms")
    settings: Mapped["ClassroomSettings"] = relationship(
        "ClassroomSettings",
        back_populates="classroom",
        uselist=False,
    )
    time_slots: Mapped[list["TimeSlot"]] = relationship(
        "TimeSlot",
        back_populates="classroom",
    )
    google_form_connections: Mapped[list["GoogleFormConnection"]] = relationship(
        "GoogleFormConnection",
        back_populates="classroom",
    )
    user_classrooms: Mapped[list["UserClassroom"]] = relationship(
        "UserClassroom",
        back_populates="classroom",
    )
    teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher",
        back_populates="classroom",
    )
    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="classroom",
    )
    terms: Mapped[list["Term"]] = relationship(
        "Term",
        back_populates="classroom",
    )
    policy_templates: Mapped[list["PolicyTemplate"]] = relationship(
        "PolicyTemplate",
        back_populates="classroom",
    )


class UserClassroom(Base):
    """ユーザー-教室中間テーブル"""
    __tablename__ = "user_classrooms"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        primary_key=True,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        primary_key=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_classrooms")
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="user_classrooms")


class UserArea(Base):
    """ユーザー-エリア中間テーブル"""
    __tablename__ = "user_areas"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        primary_key=True,
    )
    area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("areas.area_id"),
        primary_key=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_areas")
    area: Mapped["Area"] = relationship("Area", back_populates="user_areas")


class ClassroomSettings(Base, TimestampMixin):
    """教室設定テーブル"""
    __tablename__ = "classroom_settings"

    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        primary_key=True,
    )
    booth_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    weekday_slots: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
    )
    saturday_slots: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )
    operating_days: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="settings")


class TimeSlot(Base):
    """時間枠テーブル"""
    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint("classroom_id", "day_type", "slot_number", name="uq_time_slots"),
    )

    time_slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        nullable=False,
    )
    day_type: Mapped[DayType] = mapped_column(
        Enum(DayType, name="day_type", create_type=True),
        nullable=False,
    )
    slot_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="time_slots")


class GoogleFormConnection(Base, TimestampMixin):
    """Google Form連携設定テーブル"""
    __tablename__ = "google_form_connections"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.classroom_id"),
        nullable=False,
    )
    data_type: Mapped[GoogleFormDataType] = mapped_column(
        Enum(GoogleFormDataType, name="google_form_data_type", create_type=True),
        nullable=False,
    )
    spreadsheet_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sheet_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    column_mapping: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    oauth_token_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    classroom: Mapped["Classroom"] = relationship("Classroom", back_populates="google_form_connections")
