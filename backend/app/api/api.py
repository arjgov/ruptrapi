from fastapi import APIRouter
from app.api.v1 import organizations, services, users, consumers, analysis

api_router = APIRouter()

api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(consumers.router, prefix="/consumers", tags=["Consumers"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
