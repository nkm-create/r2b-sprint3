"""データベースENUM定義"""
import enum


class UserRole(str, enum.Enum):
    """ユーザー役割"""
    CLASSROOM_MANAGER = "classroom_manager"
    AREA_MANAGER = "area_manager"
    SYSTEM_ADMIN = "system_admin"


class UserStatus(str, enum.Enum):
    """ユーザーステータス"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ClassroomStatus(str, enum.Enum):
    """教室ステータス"""
    OPERATING = "operating"
    CLOSED = "closed"


class DayType(str, enum.Enum):
    """曜日種別"""
    WEEKDAY = "weekday"
    SATURDAY = "saturday"


class DayOfWeek(str, enum.Enum):
    """曜日"""
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"


class GoogleFormDataType(str, enum.Enum):
    """Google Formデータ種別"""
    TEACHER_SHIFT = "teacher_shift"
    STUDENT_PREFERENCE = "student_preference"


class Gender(str, enum.Enum):
    """性別"""
    MALE = "male"
    FEMALE = "female"


class PreferredGender(str, enum.Enum):
    """希望講師性別"""
    MALE = "male"
    FEMALE = "female"
    ANY = "any"


class Grade(str, enum.Enum):
    """学年"""
    ELE1 = "ele1"
    ELE2 = "ele2"
    ELE3 = "ele3"
    ELE4 = "ele4"
    ELE5 = "ele5"
    ELE6 = "ele6"
    JHS1 = "jhs1"
    JHS2 = "jhs2"
    JHS3 = "jhs3"
    HS1 = "hs1"
    HS2 = "hs2"
    HS3 = "hs3"


class UniversityRank(str, enum.Enum):
    """大学ランク"""
    A = "A"
    B = "B"
    C = "C"


class AspirationLevel(str, enum.Enum):
    """志望レベル"""
    A = "A"
    B = "B"
    C = "C"


class EnrollmentPurpose(str, enum.Enum):
    """通塾目的"""
    HS_EXAM = "hs_exam"
    JHS_EXAM = "jhs_exam"
    INTERNAL = "internal"
    REMEDIAL = "remedial"
    OTHER = "other"


class TeacherStatus(str, enum.Enum):
    """講師ステータス"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class StudentStatus(str, enum.Enum):
    """生徒ステータス"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class TeacherChangeReason(str, enum.Enum):
    """講師変更理由"""
    SCHEDULE_CHANGE = "SCHEDULE_CHANGE"
    SUBJECT_CHANGE = "SUBJECT_CHANGE"
    GRADE_CHANGE = "GRADE_CHANGE"
    NG_CHANGE = "NG_CHANGE"
    STATUS_CHANGE = "STATUS_CHANGE"
    INITIAL = "INITIAL"
    OTHER = "OTHER"


class StudentChangeReason(str, enum.Enum):
    """生徒変更理由"""
    COURSE_CHANGE = "COURSE_CHANGE"
    GRADE_UP = "GRADE_UP"
    PREFERENCE_CHANGE = "PREFERENCE_CHANGE"
    GOAL_CHANGE = "GOAL_CHANGE"
    STATUS_CHANGE = "STATUS_CHANGE"
    INITIAL = "INITIAL"
    OTHER = "OTHER"


class TeacherPreferenceValue(str, enum.Enum):
    """講師シフト希望値"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class StudentPreferenceValue(str, enum.Enum):
    """生徒受講希望値"""
    PREFERRED = "preferred"
    UNAVAILABLE = "unavailable"
    POSSIBLE = "possible"


class TermStatus(str, enum.Enum):
    """タームステータス"""
    CREATING = "creating"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class ConstraintTargetType(str, enum.Enum):
    """制約対象種別"""
    TEACHER = "teacher"
    STUDENT = "student"
    CLASSROOM = "classroom"


class ConstraintType(str, enum.Enum):
    """制約種別"""
    MAX_SLOTS = "max_slots"
    MIN_SLOTS = "min_slots"
    MAX_CONSECUTIVE = "max_consecutive"
    SUBJECT_LIMIT = "subject_limit"
    DAY_LIMIT = "day_limit"
    PREFERRED_TEACHER = "preferred_teacher"
    NG_TEACHER = "ng_teacher"
    GENDER_PREFERENCE = "gender_preference"
    BOOTH_CAPACITY = "booth_capacity"


class PolicyType(str, enum.Enum):
    """ポリシー種別"""
    P001 = "P001"
    P002 = "P002"
    P003 = "P003"
    P004 = "P004"
    P005 = "P005"
    P006 = "P006"


class ScheduleStatus(str, enum.Enum):
    """時間割ステータス"""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class SlotType(str, enum.Enum):
    """コマ種別"""
    ONE_TO_TWO = "one_to_two"
    ONE_TO_ONE = "one_to_one"


class SlotStatus(str, enum.Enum):
    """コマステータス"""
    SCHEDULED = "scheduled"
    ABSENT = "absent"
    SUBSTITUTED = "substituted"


class AbsentType(str, enum.Enum):
    """欠席種別"""
    TEACHER = "teacher"
    STUDENT = "student"


class SubstitutionStatus(str, enum.Enum):
    """振替ステータス"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SubstitutionType(str, enum.Enum):
    """振替種別"""
    RESCHEDULE = "reschedule"
    SUBSTITUTE = "substitute"


class NgCreatedBy(str, enum.Enum):
    """NG設定者"""
    TEACHER = "teacher"
    STUDENT = "student"


class NotificationType(str, enum.Enum):
    """通知種別"""
    FULFILLMENT_LOW = "fulfillment_low"
    UNANSWERED_PREFERENCE = "unanswered_preference"
    TERM_DEADLINE = "term_deadline"
    SCHEDULE_CONFLICT = "schedule_conflict"


class Severity(str, enum.Enum):
    """重要度"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class GradeCategory(str, enum.Enum):
    """学年カテゴリ"""
    ELEMENTARY = "elementary"
    JUNIOR_HIGH = "junior_high"
    HIGH_SCHOOL = "high_school"


class SubjectCategory(str, enum.Enum):
    """科目カテゴリ"""
    ENGLISH = "english"
    MATH = "math"
    JAPANESE = "japanese"
    SCIENCE = "science"
    SOCIAL = "social"
