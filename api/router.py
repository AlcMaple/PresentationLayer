from fastapi import APIRouter
from api.categories import router as categories_router

router = APIRouter()
router.include_router(categories_router)
