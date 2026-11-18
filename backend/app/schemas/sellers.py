from pydantic import BaseModel, ValidationInfo, field_validator

from app.enums.permission import Permission
from app.models import User
from app.schemas.common import ApiModel, Email, Locale, Name, NewPassword, Phone, StoreDateTime


class CreateSellerRequest(ApiModel):
    name: Name
    email: Email
    phone: Phone = None
    locale: Locale = "en"
    password: NewPassword
    password_confirmation: str
    permissions: list[Permission] = []

    @field_validator("password_confirmation")
    @classmethod
    def _confirm(cls, value: str, info: ValidationInfo) -> str:
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("validation.password_mismatch")
        return value


class UpdateSellerRequest(ApiModel):
    name: Name | None = None
    email: Email | None = None
    phone: Phone = None
    locale: Locale | None = None


class SellerPermissionsRequest(ApiModel):
    permissions: list[Permission]


class SellerStatusRequest(ApiModel):
    is_active: bool


class ResetSellerPasswordRequest(ApiModel):
    password: NewPassword
    password_confirmation: str

    @field_validator("password_confirmation")
    @classmethod
    def _confirm(cls, value: str, info: ValidationInfo) -> str:
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("validation.password_mismatch")
        return value


class SellerOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    locale: str
    is_active: bool
    permissions: list[str]
    active_sessions: int
    last_login_at: StoreDateTime | None
    created_at: StoreDateTime

    @classmethod
    def from_user(cls, user: User, active_sessions: int = 0) -> "SellerOut":
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            locale=user.locale,
            is_active=user.is_active,
            permissions=sorted(p.value for p in user.permission_set),
            active_sessions=active_sessions,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )


class PermissionOut(BaseModel):
    key: str
    label: str
    depends_on: list[str]


class PermissionGroupOut(BaseModel):
    key: str
    label: str
    permissions: list[PermissionOut]
