from fastapi import APIRouter, Response, status
from sqlalchemy import delete, select

from app.api.deps import CurrentUser, DbSession
from app.core.clock import utc_now
from app.core.i18n import t
from app.models import DeviceToken
from app.schemas.auth import DeviceTokenRequest
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=MessageResponse, summary="Register for push")
def register_device(body: DeviceTokenRequest, user: CurrentUser, db: DbSession) -> MessageResponse:
    """A token moves to whoever logged in last on that device."""
    device = db.scalar(select(DeviceToken).where(DeviceToken.token == body.token))
    if device is None:
        device = DeviceToken(token=body.token)
        db.add(device)
    device.user_id = user.id
    device.platform = body.platform.value
    device.last_seen_at = utc_now()
    db.commit()
    return MessageResponse(message=t("messages.device_registered"))


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT, summary="Stop push to this device")
def remove_device(token: str, user: CurrentUser, db: DbSession) -> Response:
    db.execute(delete(DeviceToken).where(DeviceToken.token == token, DeviceToken.user_id == user.id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
