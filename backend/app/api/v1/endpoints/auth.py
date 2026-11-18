from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.deps import CurrentSessionId, CurrentUser
from app.core.i18n import t
from app.core.rate_limit import RateLimitRule, rate_limiter
from app.schemas.auth import (
    AuthUserOut,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    UpdateProfileRequest,
)
from app.schemas.common import DataResponse, MessageResponse
from app.services.audit import ClientContext
from app.services.auth_service import AuthService
from app.services.password_reset import PasswordResetService

router = APIRouter(prefix="/auth", tags=["auth"])

Auth = Annotated[AuthService, Depends()]
Resets = Annotated[PasswordResetService, Depends()]


def _limit(rule: RateLimitRule, email: str, context: ClientContext) -> None:
    rate_limiter.hit(rule, f"{email.strip()}|{context.ip_address}")


@router.post("/login", response_model=DataResponse[LoginResponse], summary="Staff login (email + password)")
def login(body: LoginRequest, context: ClientContext, auth: Auth) -> DataResponse[LoginResponse]:
    rate_limiter.hit(RateLimitRule.LOGIN_IP, context.ip_address or "unknown")
    _limit(RateLimitRule.LOGIN, body.email, context)
    tokens, user = auth.login(body.email, body.password, body.device_name)
    return DataResponse(data=LoginResponse(**tokens.model_dump(), user=AuthUserOut.from_user(user)))


@router.post("/refresh", response_model=DataResponse[TokenPair], summary="New tokens from a refresh token")
def refresh(body: RefreshRequest, auth: Auth) -> DataResponse[TokenPair]:
    return DataResponse(data=auth.refresh(body.refresh_token))


@router.post("/logout", response_model=MessageResponse, summary="Log out this device")
def logout(user: CurrentUser, session_id: CurrentSessionId, auth: Auth) -> MessageResponse:
    auth.logout(user, session_id)
    return MessageResponse(message=t("messages.logged_out"))


@router.post("/logout-all", response_model=MessageResponse, summary="Log out every device")
def logout_all(user: CurrentUser, auth: Auth) -> MessageResponse:
    auth.logout_all(user)
    return MessageResponse(message=t("messages.logged_out_all"))


@router.get("/me", response_model=DataResponse[AuthUserOut], summary="Logged-in user with role and permissions")
def me(user: CurrentUser) -> DataResponse[AuthUserOut]:
    return DataResponse(data=AuthUserOut.from_user(user))


@router.patch("/me", response_model=DataResponse[AuthUserOut], summary="Update own name, phone or language")
def update_me(body: UpdateProfileRequest, user: CurrentUser, auth: Auth) -> DataResponse[AuthUserOut]:
    user = auth.update_profile(user, body.model_dump(exclude_unset=True))
    return DataResponse(data=AuthUserOut.from_user(user))


@router.put("/password", response_model=MessageResponse, summary="Change password (signs out other devices)")
def change_password(
    body: ChangePasswordRequest, user: CurrentUser, session_id: CurrentSessionId, auth: Auth
) -> MessageResponse:
    auth.change_password(user, session_id, body.current_password, body.password)
    return MessageResponse(message=t("messages.password_changed"))


@router.post("/forgot-password", response_model=MessageResponse, summary="Email a reset code")
def forgot_password(
    body: ForgotPasswordRequest,
    background: BackgroundTasks,
    context: ClientContext,
    resets: Resets,
) -> MessageResponse:
    _limit(RateLimitRule.PASSWORD_RESET, body.email, context)
    resets.send_code(body.email, background)
    return MessageResponse(message=t("messages.reset_code_sent"))


@router.post("/reset-password", response_model=MessageResponse, summary="Set a new password with the emailed code")
def reset_password(body: ResetPasswordRequest, context: ClientContext, resets: Resets) -> MessageResponse:
    _limit(RateLimitRule.PASSWORD_RESET, body.email, context)
    resets.reset(body.email, body.code, body.password)
    return MessageResponse(message=t("messages.password_reset"))
