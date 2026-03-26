"""SQLAlchemy ORMモデル"""
from app.models.enums import (
    AbsentType,
    AspirationLevel,
    ClassroomStatus,
    ConstraintTargetType,
    ConstraintType,
    DayOfWeek,
    DayType,
    EnrollmentPurpose,
    Gender,
    GoogleFormDataType,
    Grade,
    GradeCategory,
    NgCreatedBy,
    NotificationType,
    PolicyType,
    PreferredGender,
    ScheduleStatus,
    Severity,
    SlotStatus,
    SlotType,
    StudentChangeReason,
    StudentPreferenceValue,
    StudentStatus,
    SubjectCategory,
    SubstitutionStatus,
    SubstitutionType,
    TeacherChangeReason,
    TeacherPreferenceValue,
    TeacherStatus,
    TermStatus,
    UniversityRank,
    UserRole,
    UserStatus,
)

from app.models.users import (
    User,
    PasswordResetToken,
    RefreshToken,
)

from app.models.classrooms import (
    Area,
    Classroom,
    ClassroomSettings,
    GoogleFormConnection,
    TimeSlot,
    UserArea,
    UserClassroom,
)

from app.models.teachers import (
    Teacher,
    TeacherGrade,
    TeacherSubject,
)

from app.models.students import (
    Student,
    StudentSubject,
)

from app.models.subjects import (
    NgRelation,
    Subject,
)

from app.models.preferences import (
    StudentPreference,
    TeacherShiftPreference,
)

from app.models.schedules import (
    Absence,
    Policy,
    PolicyTemplate,
    Schedule,
    ScheduleSlot,
    Substitution,
    Term,
    TermConstraint,
)

from app.models.notifications import (
    AuditLog,
    Notification,
)

__all__ = [
    # Enums
    "AbsentType",
    "AspirationLevel",
    "ClassroomStatus",
    "ConstraintTargetType",
    "ConstraintType",
    "DayOfWeek",
    "DayType",
    "EnrollmentPurpose",
    "Gender",
    "GoogleFormDataType",
    "Grade",
    "GradeCategory",
    "NgCreatedBy",
    "NotificationType",
    "PolicyType",
    "PreferredGender",
    "ScheduleStatus",
    "Severity",
    "SlotStatus",
    "SlotType",
    "StudentChangeReason",
    "StudentPreferenceValue",
    "StudentStatus",
    "SubjectCategory",
    "SubstitutionStatus",
    "SubstitutionType",
    "TeacherChangeReason",
    "TeacherPreferenceValue",
    "TeacherStatus",
    "TermStatus",
    "UniversityRank",
    "UserRole",
    "UserStatus",
    # Users
    "User",
    "PasswordResetToken",
    "RefreshToken",
    # Classrooms
    "Area",
    "Classroom",
    "ClassroomSettings",
    "GoogleFormConnection",
    "TimeSlot",
    "UserArea",
    "UserClassroom",
    # Teachers
    "Teacher",
    "TeacherGrade",
    "TeacherSubject",
    # Students
    "Student",
    "StudentSubject",
    # Subjects
    "NgRelation",
    "Subject",
    # Preferences
    "StudentPreference",
    "TeacherShiftPreference",
    # Schedules
    "Absence",
    "Policy",
    "PolicyTemplate",
    "Schedule",
    "ScheduleSlot",
    "Substitution",
    "Term",
    "TermConstraint",
    # Notifications
    "AuditLog",
    "Notification",
]
