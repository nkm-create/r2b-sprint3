"""Pydanticスキーマ"""
from app.schemas.base import (
    BaseSchema,
    ErrorResponse,
    PaginatedResponse,
    SoftDeleteSchema,
    SuccessResponse,
    TimestampSchema,
)
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    LoginResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenPayload,
)
from app.schemas.users import (
    PasswordChange,
    PasswordReset,
    UserBase,
    UserBriefResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.schemas.dashboard import (
    CoverageStatus,
    DashboardResponse,
    FulfillmentSummary,
    HeatmapCell,
    HeatmapResponse,
    HeatmapStatus,
    NotificationItem,
    NotificationResponse,
    PersonnelSummary,
    SubjectCoverage,
    SubjectCoverageResponse,
    SupplyDemandBalance,
    SupplyDemandResponse,
    TermInfo,
)

__all__ = [
    # Base
    "BaseSchema",
    "ErrorResponse",
    "PaginatedResponse",
    "SoftDeleteSchema",
    "SuccessResponse",
    "TimestampSchema",
    # Auth
    "CurrentUser",
    "LoginRequest",
    "LoginResponse",
    "PasswordResetConfirm",
    "PasswordResetRequest",
    "RefreshTokenRequest",
    "TokenPayload",
    # Users
    "PasswordChange",
    "PasswordReset",
    "UserBase",
    "UserBriefResponse",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    # Dashboard
    "CoverageStatus",
    "DashboardResponse",
    "FulfillmentSummary",
    "HeatmapCell",
    "HeatmapResponse",
    "HeatmapStatus",
    "NotificationItem",
    "NotificationResponse",
    "PersonnelSummary",
    "SubjectCoverage",
    "SubjectCoverageResponse",
    "SupplyDemandBalance",
    "SupplyDemandResponse",
    "TermInfo",
]
