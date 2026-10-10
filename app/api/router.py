from fastapi import APIRouter

from app.api.v1.v1_router import v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/api")

__all__ = ["router"]
