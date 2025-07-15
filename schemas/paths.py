from pydantic import BaseModel, Field, ValidationError, model_validator, field_validator
from typing import Optional, List


class PathsBase(BaseModel):
    """路径基础模型"""

    id: Optional[int] = None
    code: str = Field(max_length=50, description="路径编码")
    name: str = Field(max_length=200, description="路径名称")


class PathsCreate(PathsBase):
    """路径创建模型"""

    category_code: str = None
    assessment_unit_code: Optional[str] = None
    bridge_type_code: str = None
    part_code: str = None
    structure_code: Optional[str] = None
    component_type_code: Optional[str] = None
    component_form_code: Optional[str] = None
    disease_code: str = None
    scale_code: str = None
    quality_code: Optional[str] = None
    quantity_code: Optional[str] = None


class PathsUpdate(PathsBase):
    """路径更新模型"""

    category_code: str = None
    assessment_unit_code: Optional[str] = None
    bridge_type_code: str = None
    part_code: str = None
    structure_code: Optional[str] = None
    component_type_code: Optional[str] = None
    component_form_code: Optional[str] = None
    disease_code: str = None
    scale_code: str = None
    quality_code: Optional[str] = None
    quantity_code: Optional[str] = None


class PathsResponse(PathsBase):
    """路径响应模型"""

    category_code: Optional[str] = None
    category_name: Optional[str] = None
    assessment_unit_code: Optional[str] = None
    assessment_unit_name: Optional[str] = None
    bridge_type_code: Optional[str] = None
    bridge_type_name: Optional[str] = None
    part_code: Optional[str] = None
    part_name: Optional[str] = None
    structure_code: Optional[str] = None
    structure_name: Optional[str] = None
    component_type_code: Optional[str] = None
    component_type_name: Optional[str] = None
    component_form_code: Optional[str] = None
    component_form_name: Optional[str] = None
    disease_code: Optional[str] = None
    disease_name: Optional[str] = None
    scale_code: Optional[str] = None
    scale_name: Optional[str] = None
    quality_code: Optional[str] = None
    quality_name: Optional[str] = None
    quantity_code: Optional[str] = None
    quantity_name: Optional[str] = None


class PathConditions(BaseModel):
    """路径条件类"""

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


class DiseaseItem(BaseModel):
    """病害项模型"""

    disease_code: Optional[str] = None
    disease_name: Optional[str] = None
    scale_code: Optional[str] = None
    scale_name: Optional[str] = None
    quality_code: Optional[str] = None
    quality_name: Optional[str] = None
    quantity_code: Optional[str] = None
    quantity_name: Optional[str] = None


class PathsPageResponse(BaseModel):
    """路径分页响应模型"""

    items: List[PathsResponse] = Field(description="路径列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
