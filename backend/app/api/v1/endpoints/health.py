from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.clock import store_now

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    time: datetime


@router.get("/health", response_model=HealthResponse, summary="Uptime and database check")
def health(db: DbSession) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", time=store_now())
