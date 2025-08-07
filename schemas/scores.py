from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from decimal import Decimal

from models.enums import CalculationMode


class ScoreListRequest(BaseModel):
    """评分列表查询请求"""

    bridge_instance_name: str = Field(..., description="桥梁实例名称")
    assessment_unit_instance_name: Optional[str] = Field(
        None, description="评定单元实例名称"
    )
    # assessment_unit_id: Optional[str] = Field(None, description="评定单元ID")
    bridge_type_id: int = Field(..., description="桥梁类型ID")


class ScoreItemData(BaseModel):
    """评分数据项"""

    part_id: int = Field(..., description="部位ID")
    part_name: str = Field(..., description="部位名称")
    component_type_id: int = Field(..., description="部件类型ID")
    component_type_name: str = Field(..., description="部件类型名称")
    weight: Decimal = Field(..., description="权重")
    component_count: int = Field(..., description="构件数量")
    custom_component_count: int = Field(..., description="自定义构件数量")
    adjusted_weight: Decimal = Field(..., description="调整后权重")


class ScoreListPageResponse(BaseModel):
    """评分列表分页响应"""

    items: List[ScoreItemData] = Field(..., description="数据列表")
    total: int = Field(..., description="总数")
    # page: int = Field(..., description="当前页码")
    # size: int = Field(..., description="每页数量")


class ScoresCascadeOptionsResponse(BaseModel):
    """评分级联选项响应模型"""

    bridge_instance_options: List[Dict[str, Any]] = Field(
        default_factory=list, description="桥梁实例名称选项"
    )
    assessment_unit_instance_options: List[Dict[str, Any]] = Field(
        default_factory=list, description="评定单元实例名称选项"
    )
    bridge_type_options: List[Dict[str, Any]] = Field(
        default_factory=list, description="桥梁类型选项"
    )


# 自定义构件数量数据项
class CustomComponentCountItem(BaseModel):
    """自定义构件数量数据项"""

    part_id: int = Field(..., description="部位ID")
    component_type_id: int = Field(..., description="部件类型ID")
    custom_component_count: int = Field(..., ge=0, description="自定义构件数量")


# 权重分配计算请求
class WeightAllocationRequest(BaseModel):
    """权重分配计算请求"""

    bridge_instance_name: str = Field(..., description="桥梁实例名称")
    bridge_type_id: int = Field(..., description="桥梁类型ID")
    assessment_unit_instance_name: Optional[str] = Field(
        None, description="评定单元实例名称"
    )

    calculation_mode: CalculationMode = Field(..., description="计算方式")
    custom_component_counts: Optional[List[CustomComponentCountItem]] = Field(
        None, description="自定义构件数量数据"
    )

    @model_validator(mode="after")
    @classmethod
    def validate_custom_component_counts(cls, values):
        """验证自定义构件数量数据"""
        calculation_mode = values.calculation_mode
        custom_component_counts = values.custom_component_counts
        if calculation_mode == CalculationMode.CUSTOM and not custom_component_counts:
            raise ValueError("使用自定义计算方式时，必须提供自定义构件数量数据")
        return values


# 权重分配计算响应
class WeightAllocationResponse(ScoreListPageResponse):
    """权重分配计算响应"""

    calculation_mode: CalculationMode = Field(..., description="计算方式")
