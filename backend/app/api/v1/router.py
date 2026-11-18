from fastapi import APIRouter

from app.api.v1.endpoints import admin_sellers, auth, devices, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(admin_sellers.router)
# Later phases: categories, products, inventory, expiry, public catalogue, reports
