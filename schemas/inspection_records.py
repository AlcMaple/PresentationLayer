from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict
from datetime import datetime


class InspectionRecordsCreate(BaseModel):
    """检查记录创建模型"""

    # 前7层路径字段
    category_id: int = Field(..., description="桥梁ID")
    assessment_unit_id: Optional[int] = Field(None, description="评定单元ID")
    bridge_type_id: int = Field(..., description="桥梁类型ID")
    part_id: int = Field(..., description="部位ID")
    structure_id: Optional[int] = Field(..., description="结构类型ID")
    component_type_id: int = Field(..., description="部件类型ID")
    component_form_id: int = Field(..., description="构件形式ID")

    # 病害和标度数据
    damage_type_code: str = Field(..., description="病害类型编码", max_length=50)
    scale_code: str = Field(..., description="标度编码", max_length=50)

    # 检查数据字段
    damage_location: Optional[str] = Field(None, description="病害位置")
    damage_description: Optional[str] = Field(None, description="病害描述")
    image_url: Optional[str] = Field(None, description="图片URL")

    # 构件名称字段
    component_name: Optional[str] = Field(None, description="构件名称", max_length=100)


class InspectionRecordsUpdate(BaseModel):
    """检查记录更新模型"""

    # 病害和标度数据
    damage_type_code: str = Field(None, description="病害类型编码", max_length=50)
    scale_code: str = Field(None, description="标度编码", max_length=50)

    # 检查数据字段
    damage_location: Optional[str] = Field(None, description="病害位置")
    damage_description: Optional[str] = Field(None, description="病害描述")
    image_url: Optional[str] = Field(None, description="图片URL")

    # 构件名称字段
    component_name: Optional[str] = Field(None, description="构件名称", max_length=100)


class PathValidationRequest(BaseModel):
    """路径验证请求模型"""

    category_id: int = Field(..., description="桥梁ID")
    assessment_unit_id: int = Field(..., description="评定单元ID")
    bridge_type_id: int = Field(..., description="桥梁类型ID")
    part_id: int = Field(..., description="部位ID")
    structure_id: int = Field(..., description="结构类型ID")
    component_type_id: int = Field(..., description="部件类型ID")
    component_form_id: int = Field(..., description="构件形式ID")


class DamageTypeOption(BaseModel):
    """病害类型选项"""

    code: str
    name: str


class ScaleOption(BaseModel):
    """标度选项"""

    code: str
    name: str
    value: Optional[int] = None


class FormOptionsResponse(BaseModel):
    """表单选项响应"""

    damage_types: List[DamageTypeOption] = []
    scales_by_damage: Dict[str, List[ScaleOption]] = Field(
        default_factory=dict, description="按病害类型分组的标度选项，key为病害类型code"
    )


class DamageDetailInfo(BaseModel):
    """病害详细信息"""

    damage_type_code: str
    damage_type_name: str
    scales: List[ScaleOption] = []
    qualities: List[str] = []  # 定性描述列表
    quantities: List[str] = []  # 定量描述列表


class InspectionRecordsResponse(BaseModel):
    """检查记录响应模型"""

    id: int

    # 路径信息
    category_id: int
    category_name: Optional[str] = None
    assessment_unit_id: Optional[int] = None
    assessment_unit_name: Optional[str] = None
    bridge_type_id: int
    bridge_type_name: Optional[str] = None
    part_id: int
    part_name: Optional[str] = None
    structure_id: Optional[int] = None
    structure_name: Optional[str] = None
    component_type_id: int
    component_type_name: Optional[str] = None
    component_form_id: int
    component_form_name: Optional[str] = None

    # 病害和标度信息
    damage_type_id: int
    damage_type_code: str
    damage_type_name: Optional[str] = None
    scale_id: int
    scale_code: str
    scale_name: Optional[str] = None
    scale_value: Optional[int] = None

    # 检查数据
    damage_location: Optional[str] = None
    damage_description: Optional[str] = None
    image_url: Optional[str] = None

    # 其他信息
    created_at: datetime
    updated_at: datetime
    is_active: bool

    # 表单信息
    form_options: Optional[FormOptionsResponse] = None

    # 构件名称信息
    component_name: Optional[str] = None

    class Config:
        from_attributes = True


class DamageReferenceRequest(BaseModel):
    """病害参考信息请求"""

    category_id: int = Field(..., description="桥梁ID")
    assessment_unit_id: Optional[int] = Field(None, description="评定单元ID")
    bridge_type_id: int = Field(..., description="桥梁类型ID")
    part_id: int = Field(..., description="部位ID")
    structure_id: Optional[int] = Field(None, description="结构类型ID")
    component_type_id: int = Field(..., description="部件类型ID")
    component_form_id: int = Field(..., description="构件形式ID")
    damage_type_code: str = Field(..., description="病害类型编码")
