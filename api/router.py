from fastapi import APIRouter
from api.categories import router as categories_router
from api.assessment_units import router as assessment_units_router
from api.bridge_types import router as bridge_types_router
from api.bridge_structures import router as bridge_structures_router
from api.bridge_parts import router as bridge_parts_router
from api.bridge_component_types import router as bridge_component_types_router
from api.bridge_component_forms import router as bridge_component_forms_router
from api.bridge_diseases import router as bridge_diseases_router
from api.bridge_qualities import router as bridge_qualities_router
from api.bridge_quantities import router as bridge_quantities_router

router = APIRouter()
router.include_router(categories_router)
router.include_router(assessment_units_router)
router.include_router(bridge_types_router)
router.include_router(bridge_structures_router)
router.include_router(bridge_parts_router)
router.include_router(bridge_component_types_router)
router.include_router(bridge_component_forms_router)
router.include_router(bridge_diseases_router)
router.include_router(bridge_qualities_router)
router.include_router(bridge_quantities_router)
