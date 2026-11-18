from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_catalogue,
    admin_sellers,
    admin_settings,
    auth,
    categories,
    dashboard,
    devices,
    health,
    inventory,
    lookups,
    notifications,
    products,
    public,
    reports,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(dashboard.router)
api_router.include_router(categories.router)
api_router.include_router(lookups.router)
api_router.include_router(products.router)
api_router.include_router(inventory.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
api_router.include_router(admin_sellers.router)
api_router.include_router(admin_catalogue.router)
api_router.include_router(admin_settings.router)
api_router.include_router(public.router)
