from fastapi import APIRouter
from api.bridge_base import router as bridge_router

router = APIRouter()
router.include_router(bridge_router)
