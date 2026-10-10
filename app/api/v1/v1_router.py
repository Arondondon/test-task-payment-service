from fastapi import APIRouter

from app.api.v1.endpoints import payment_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(payment_router)

__all__ = ["v1_router"]
