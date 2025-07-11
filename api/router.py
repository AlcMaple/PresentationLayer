from fastapi import APIRouter
from api.categories import router as categories_router
from api.assessment_units import router as assessment_units_router

router = APIRouter()
router.include_router(categories_router)
router.include_router(assessment_units_router)
