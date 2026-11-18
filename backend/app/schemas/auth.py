from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.core.constants import DEVICE_NAME_MAX_LENGTH, DEVICE_TOKEN_MAX_LENGTH, TOKEN_TYPE
from app.enums.device import DevicePlatform
from app.models import User
from app.schemas.common import ApiModel, Locale, Name, NewPassword, Phone, StoreDateTime


def _confirm(value: str, info: ValidationInfo) -> str:
    if "password" in info.data and value != info.data["password"]:
        raise ValueError("validation.password_mismatch")
    return value


# --- Requests -------------------------------------------------------------------------------------


class LoginRequest(ApiModel):
    email: str = Field(max_length=191)  # not format-checked: a wrong email just fails to log in
    password: str = Field(max_length=128)
    device_name: str = Field(min_length=1, max_length=DEVICE_NAME_MAX_LENGTH)


class RefreshRequest(ApiModel):
    refresh_token: str = Field(min_length=1, max_length=255)


class UpdateProfileRequest(ApiModel):
    """Email is the login identity, so only the admin can change it (for sellers)."""

    name: Name | None = None
    phone: Phone = None
    locale: Locale | None = None


class ChangePasswordRequest(ApiModel):
    current_password: str = Field(max_length=128)
    password: NewPassword
    password_confirmation: str

    _confirm = field_validator("password_confirmation")(_confirm)

    @field_validator("password")
    @classmethod
    def _different(cls, value: str, info: ValidationInfo) -> str:
        if value == info.data.get("current_password"):
            raise ValueError("validation.password_same")
        return value


class ForgotPasswordRequest(ApiModel):
    email: str = Field(max_length=191)


class ResetPasswordRequest(ApiModel):
    email: str = Field(max_length=191)
    code: str = Field(pattern=r"^\d+$", max_length=10)
    password: NewPassword
    password_confirmation: str

    _confirm = field_validator("password_confirmation")(_confirm)


class DeviceTokenRequest(ApiModel):
    token: str = Field(min_length=1, max_length=DEVICE_TOKEN_MAX_LENGTH)
    platform: DevicePlatform


# --- Responses ------------------------------------------------------------------------------------


class AuthUserOut(BaseModel):
    """The logged-in user. `permissions` decides which screens the app shows;
    the server still checks every request on its own."""

    id: int
    name: str
    email: str
    phone: str | None
    locale: str
    role: str
    permissions: list[str]
    last_login_at: StoreDateTime | None

    @classmethod
    def from_user(cls, user: User) -> "AuthUserOut":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            locale=user.locale,
            role=user.role.name,
            permissions=sorted(p.value for p in user.permission_set),
            last_login_at=user.last_login_at,
        )


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = TOKEN_TYPE
    access_token_expires_at: StoreDateTime
    refresh_token_expires_at: StoreDateTime


class LoginResponse(TokenPair):
    user: AuthUserOut
