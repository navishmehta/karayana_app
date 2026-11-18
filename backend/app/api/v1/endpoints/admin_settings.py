"""Admin-only store settings (store name, contact details, catalogue and alert options)."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import AdminUser, DbSession
from app.schemas.common import DataResponse
from app.schemas.settings import SettingsOut, SettingsUpdate
from app.services.settings_service import SettingsService, all_settings

router = APIRouter(prefix="/admin/settings", tags=["admin"])

Settings = Annotated[SettingsService, Depends()]


@router.get("", response_model=DataResponse[SettingsOut])
def get_settings_endpoint(admin: AdminUser, db: DbSession) -> DataResponse[SettingsOut]:
    return DataResponse(data=SettingsOut.from_settings(all_settings(db, admin.store_id)))


@router.patch("", response_model=DataResponse[SettingsOut], summary="Change one or more settings")
def update_settings(body: SettingsUpdate, admin: AdminUser, settings: Settings) -> DataResponse[SettingsOut]:
    return DataResponse(data=SettingsOut.from_settings(settings.update(admin, body.to_settings())))


@router.post("/logo", response_model=DataResponse[SettingsOut], summary="Upload / replace the store logo")
def upload_logo(
    admin: AdminUser, settings: Settings, image: Annotated[UploadFile, File()]
) -> DataResponse[SettingsOut]:
    return DataResponse(data=SettingsOut.from_settings(settings.replace_logo(admin, image)))
