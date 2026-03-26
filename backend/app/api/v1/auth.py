"""認証API"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.database import get_db
from app.services.auth import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["認証"])


# リクエスト/レスポンススキーマ
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=72)


class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetExecuteRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=72)


class MessageResponse(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """ログイン"""
    auth_service = AuthService(db)

    # デバイス情報とIPアドレスを取得
    device_info = request.headers.get("User-Agent")
    ip_address = request.client.host if request.client else None

    try:
        result = await auth_service.login(
            email=body.email,
            password=body.password,
            device_info=device_info,
            ip_address=ip_address,
        )
        return result
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """アクセストークンをリフレッシュ"""
    auth_service = AuthService(db)

    try:
        result = await auth_service.refresh_access_token(body.refresh_token)
        return result
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: LogoutRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """ログアウト"""
    auth_service = AuthService(db)
    await auth_service.logout(body.refresh_token, current_user.user_id)
    return {"message": "ログアウトしました"}


@router.post("/password/change", response_model=MessageResponse)
async def change_password(
    body: PasswordChangeRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """パスワード変更"""
    auth_service = AuthService(db)

    try:
        await auth_service.change_password(
            user_id=current_user.user_id,
            current_password=body.current_password,
            new_password=body.new_password,
        )
        return {"message": "パスワードを変更しました"}
    except AuthError as e:
        status_code = status.HTTP_401_UNAUTHORIZED
        if e.code == "AUTH_005":
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={"code": e.code, "message": e.message},
        )


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    body: PasswordResetRequestBody,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """パスワードリセットリクエスト"""
    auth_service = AuthService(db)

    # トークンを取得（メール送信は別途実装）
    token = await auth_service.request_password_reset(body.email)

    # TODO: メール送信処理を実装
    # 本番環境ではトークンをメールで送信し、ここではトークンを返さない
    # if token:
    #     await send_password_reset_email(body.email, token)

    # セキュリティ上、常に同じレスポンスを返す
    return {"message": "パスワードリセットメールを送信しました"}


@router.post("/password-reset/execute", response_model=MessageResponse)
async def execute_password_reset(
    body: PasswordResetExecuteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """パスワードリセット実行"""
    auth_service = AuthService(db)

    try:
        await auth_service.execute_password_reset(
            token=body.token,
            new_password=body.new_password,
        )
        return {"message": "パスワードを変更しました"}
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser):
    """現在のユーザー情報を取得"""
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.value,
        "force_password_change": current_user.force_password_change,
    }
