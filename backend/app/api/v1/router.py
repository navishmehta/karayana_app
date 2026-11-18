from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_catalogue,
    admin_sellers,
    auth,
    categories,
    devices,
    health,
    inventory,
    lookups,
    products,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(categories.router)
api_router.include_router(lookups.router)
api_router.include_router(products.router)
api_router.include_router(inventory.router)
api_router.include_router(admin_sellers.router)
api_router.include_router(admin_catalogue.router)
# Later phases: public catalogue, reports
