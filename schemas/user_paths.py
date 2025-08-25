from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserPathsCreate(BaseModel):
    """用户路径创建模型"""

    # 基础路径字段
    category_id: int = Field(..., description="桥梁类别ID")
    assessment_unit_id: Optional[int] = Field(None, description="评定单元ID")
    bridge_type_id: int = Field(..., description="桥梁类型ID")
    part_id: int = Field(..., description="部位ID")
    structure_id: Optional[int] = Field(None, description="结构类型ID")
    component_type_id: Optional[int] = Field(None, description="部件类型ID")
    component_form_id: Optional[int] = Field(None, description="构件形式ID")

    user_id: Optional[int] = Field(None, description="用户ID")
    bridge_instance_name: str = Field(..., max_length=200, description="桥梁实例名称")
    assessment_unit_instance_name: Optional[str] = Field(
        None, max_length=200, description="评定单元实例名称"
    )


class UserPathsUpdate(BaseModel):
    """用户路径更新模型"""

    # 基础路径字段
    category_id: Optional[int] = Field(None, description="桥梁类别ID")
    assessment_unit_id: Optional[int] = Field(None, description="评定单元ID")
    bridge_type_id: Optional[int] = Field(None, description="桥梁类型ID")
    part_id: Optional[int] = Field(None, description="部位ID")
    structure_id: Optional[int] = Field(None, description="结构类型ID")
    component_type_id: Optional[int] = Field(None, description="部件类型ID")
    component_form_id: Optional[int] = Field(None, description="构件形式ID")

    bridge_instance_name: Optional[str] = Field(
        None, max_length=200, description="桥梁实例名称"
    )
    assessment_unit_instance_name: Optional[str] = Field(
        None, max_length=200, description="评定单元实例名称"
    )


class UserPathsResponse(BaseModel):
    """用户路径响应模型"""

    id: int
    user_id: Optional[int]
    bridge_instance_name: str
    assessment_unit_instance_name: Optional[str]

    # 基础路径字段
    category_id: int
    category_name: Optional[str] = None
    assessment_unit_id: Optional[int]
    assessment_unit_name: Optional[str] = None
    bridge_type_id: Optional[int]
    bridge_type_name: Optional[str] = None
    part_id: Optional[int]
    part_name: Optional[str] = None
    structure_id: Optional[int]
    structure_name: Optional[str] = None
    component_type_id: Optional[int]
    component_type_name: Optional[str] = None
    component_form_id: Optional[int]
    component_form_name: Optional[str] = None

    # 关联信息
    paths_id: Optional[int]

    # 状态
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CascadeOptionsRequest(BaseModel):
    """级联选项请求模型"""

    category_id: Optional[int] = Field(None, description="桥梁类别ID")
    assessment_unit_id: Optional[int] = Field(None, description="评定单元ID")
    bridge_type_id: Optional[int] = Field(None, description="桥梁类型ID")
    part_id: Optional[int] = Field(None, description="部位ID")
    structure_id: Optional[int] = Field(None, description="结构类型ID")
    component_type_id: Optional[int] = Field(None, description="部件类型ID")
    component_form_id: Optional[int] = Field(None, description="构件形式ID")


class CascadeOptionsResponse(BaseModel):
    """级联选项响应模型"""

    category_options: List[Dict[str, Any]]
    assessment_unit_options: List[Dict[str, Any]]
    bridge_type_options: List[Dict[str, Any]]
    part_options: List[Dict[str, Any]]
    structure_options: List[Dict[str, Any]]
    component_type_options: List[Dict[str, Any]]
    component_form_options: List[Dict[str, Any]]


class NestedPathNode(BaseModel):
    """嵌套路径节点模型"""

    id: Optional[int] = None
    name: str
    level: str  # 层级标识
    children: Optional[List["NestedPathNode"]] = None


# 启用递归模型
NestedPathNode.model_rebuild()
