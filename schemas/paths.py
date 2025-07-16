from pydantic import BaseModel, Field, ValidationError, model_validator, field_validator
from typing import Optional, List


class PathsBase(BaseModel):
    """路径基础模型"""

    code: str = Field(max_length=50, description="路径编码", example="")
    name: str = Field(max_length=200, description="路径名称", example="")


class PathsCreate(PathsBase):
    """路径创建模型"""

    category_code: str = Field(
        ..., max_length=50, description="路径类别编码", example=""
    )
    assessment_unit_code: Optional[str] = Field(
        None, max_length=50, description="评定单元编码", example=""
    )
    bridge_type_code: str = Field(
        ..., max_length=50, description="桥梁类型编码", example=""
    )
    part_code: str = Field(..., max_length=50, description="部件编码", example="")
    structure_code: Optional[str] = Field(
        None, max_length=50, description="结构编码", example=""
    )
    component_type_code: Optional[str] = Field(
        None, max_length=50, description="构件类型编码", example=""
    )
    component_form_code: Optional[str] = Field(
        None, max_length=50, description="构件形式编码", example=""
    )
    disease_code: str = Field(..., max_length=50, description="病害编码", example="")
    scale_code: str = Field(..., max_length=50, description="病害等级编码", example="")
    quality_code: Optional[str] = Field(
        None, max_length=50, description="质量编码", example=""
    )
    quantity_code: Optional[str] = Field(
        None, max_length=50, description="数量编码", example=""
    )


class PathsUpdate(PathsBase):
    """路径更新模型"""

    category_code: str = Field(
        None, max_length=50, description="路径类别编码", example=""
    )
    assessment_unit_code: Optional[str] = Field(
        None, max_length=50, description="评定单元编码", example=""
    )
    bridge_type_code: str = Field(
        ..., max_length=50, description="桥梁类型编码", example=""
    )
    part_code: str = Field(..., max_length=50, description="部件编码", example="")
    structure_code: Optional[str] = Field(
        None, max_length=50, description="结构编码", example=""
    )
    component_type_code: Optional[str] = Field(
        None, max_length=50, description="构件类型编码", example=""
    )
    component_form_code: Optional[str] = Field(
        None, max_length=50, description="构件形式编码", example=""
    )
    disease_code: str = Field(..., max_length=50, description="病害编码", example="")
    scale_code: str = Field(..., max_length=50, description="病害等级编码", example="")
    quality_code: Optional[str] = Field(
        None, max_length=50, description="质量编码", example=""
    )
    quantity_code: Optional[str] = Field(
        None, max_length=50, description="数量编码", example=""
    )


class PathsResponse(PathsBase):
    """路径响应模型"""

    id: int = Field(description="路径ID")
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
