from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal


class ScoreListRequest(BaseModel):
    """评分列表查询请求"""

    bridge_instance_name: str = Field(..., description="桥梁实例名称")
    assessment_unit_instance_name: Optional[str] = Field(
        None, description="评定单元实例名称"
    )
    assessment_unit_id: Optional[str] = Field(None, description="评定单元ID")
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
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
