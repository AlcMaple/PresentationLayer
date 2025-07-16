from fastapi import APIRouter
from .categories import router as categories_router
from .assessment_units import router as assessment_units_router
from .bridge_types import router as bridge_types_router
from .bridge_structures import router as bridge_structures_router
from .bridge_parts import router as bridge_parts_router
from .bridge_component_types import router as bridge_component_types_router
from .bridge_component_forms import router as bridge_component_forms_router
from .bridge_diseases import router as bridge_diseases_router
from .bridge_qualities import router as bridge_qualities_router
from .bridge_quantities import router as bridge_quantities_router
from .bridge_scales import router as bridge_scales_router
from .paths import router as paths_router

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
router.include_router(bridge_scales_router)

router_paths = APIRouter()
router_paths.include_router(paths_router)