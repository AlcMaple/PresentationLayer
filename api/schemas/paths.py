from pydantic import BaseModel, Field, ValidationError, model_validator, field_validator
from typing import Optional
from datetime import datetime
from models.enums import ScalesType


class PathConditions(BaseModel):
    """路径条件类"""

    # ID 条件
    id: Optional[int] = None
    category_id: Optional[int] = None
    assessment_unit_id: Optional[int] = None
    bridge_type_id: Optional[int] = None
    part_id: Optional[int] = None
    structure_id: Optional[int] = None
    component_type_id: Optional[int] = None
    component_form_id: Optional[int] = None
    disease_id: Optional[int] = None
    scale_id: Optional[int] = None
    quality_id: Optional[int] = None
    quantity_id: Optional[int] = None

    # NAME条件
    category_name: Optional[str] = None
    assessment_unit_name: Optional[str] = None
    bridge_type_name: Optional[str] = None
    part_name: Optional[str] = None
    structure_name: Optional[str] = None
    component_type_name: Optional[str] = None
    component_form_name: Optional[str] = None
    disease_name: Optional[str] = None
    scale_name: Optional[str] = None
    quality_name: Optional[str] = None
    quantity_name: Optional[str] = None

    # CODE条件
    category_code: Optional[str] = None
    assessment_unit_code: Optional[str] = None
    bridge_type_code: Optional[str] = None
    part_code: Optional[str] = None
    structure_code: Optional[str] = None
    component_type_code: Optional[str] = None
    component_form_code: Optional[str] = None
    disease_code: Optional[str] = None
    scale_code: Optional[str] = None
    quality_code: Optional[str] = None
    quantity_code: Optional[str] = None
