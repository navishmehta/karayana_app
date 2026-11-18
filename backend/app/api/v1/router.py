from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()
api_router.include_router(health.router)
# Later phases: auth, sellers, categories, products, inventory, expiry, public catalogue, reports
