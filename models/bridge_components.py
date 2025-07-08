from sqlmodel import SQLModel, Field, Index
from typing import Optional
from datetime import datetime

from .base import BaseModel
from .enums import ScalesType
from .categories import Categories


class BridgeComponentBase(BaseModel):
    name: str = Field(description="名称")
    code: Optional[str] = Field(description="编码", default=None, unique=True)
    description: Optional[str] = Field(description="描述", default=None)
    sort_order: int = Field(description="排序", default=0)
    is_active: bool = Field(description="是否启用", default=True)


# 桥梁类型表
class BridgeTypes(BridgeComponentBase, table=True):
    __tablename__ = "bridge_types"

    id: Optional[int] = Field(default=None, primary_key=True, description="桥梁主键ID")
    category_id: Optional[int] = Field(
        default=None, foreign_key="categories.id", description="分类ID"
    )

    __table_args__ = (
        Index("idx_bridge_types_code", "code"),
        Index("idx_bridge_types_active", "is_active"),
    )


# 部位表
class BridgeParts(BridgeComponentBase, table=True):
    __tablename__ = "bridge_parts"

    id: Optional[int] = Field(default=None, primary_key=True, description="部位主键ID")

    __table_args__ = (
        Index("idx_bridge_parts_code", "code"),
        Index("idx_bridge_parts_active", "is_active"),
    )


# 结构类型表
class BridgeStructures(BridgeComponentBase, table=True):
    __tablename__ = "bridge_structures"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="结构类型主键ID"
    )

    __table_args__ = (
        Index("idx_bridge_structures_code", "code"),
        Index("idx_bridge_structures_active", "is_active"),
    )


# 部件类型表
class BridgeComponentTypes(BridgeComponentBase, table=True):
    __tablename__ = "bridge_component_types"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="部件类型主键ID"
    )

    __table_args__ = (
        Index("idx_bridge_component_types_code", "code"),
        Index("idx_bridge_component_types_active", "is_active"),
    )


# 构件形式表
class BridgeComponentForms(BridgeComponentBase, table=True):
    __tablename__ = "bridge_component_forms"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="构件形式主键ID"
    )

    __table_args__ = (
        Index("idx_bridge_component_forms_code", "code"),
        Index("idx_bridge_component_forms_active", "is_active"),
    )


# 病害类型表
class BridgeDiseases(BridgeComponentBase, table=True):
    __tablename__ = "bridge_diseases"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="病害类型主键ID"
    )

    __table_args__ = (
        Index("idx_bridge_diseases_code", "code"),
        Index("idx_bridge_diseases_active", "is_active"),
    )


# 标度表
class BridgeScales(BridgeComponentBase, table=True):
    __tablename__ = "bridge_scales"

    id: Optional[int] = Field(default=None, primary_key=True, description="标度主键ID")
    scale_type: ScalesType = Field(
        description="标度类型：NUMERIC(数值)/PERCENTAGE(百分比)/RANGE(范围)/TEXT(文本)"
    )
    scale_value: Optional[int] = Field(default=None, description="标度值")
    min_value: Optional[int] = Field(default=None, description="范围最小值")
    max_value: Optional[int] = Field(default=None, description="范围最大值")
    unit: Optional[str] = Field(default=None, description="单位")
    display_text: Optional[str] = Field(default=None, description="显示文本")

    __table_args__ = (
        Index("idx_bridge_scales_code", "code"),
        Index("idx_bridge_scales_active", "is_active"),
        Index("idx_bridge_scales_value", "scale_value"),
        Index("idx_bridge_scales_type", "scale_type"),
    )


# 定性描述表
class BridgeQualities(BridgeComponentBase, table=True):
    __tablename__ = "bridge_qualities"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="定性描述主键ID"
    )

    __table_args__ = (
        Index("idx_bridge_qualities_code", "code"),
        Index("idx_bridge_qualities_active", "is_active"),
    )


# 定量描述
class BridgeQuantities(BridgeComponentBase, table=True):
    __tablename__ = "bridge_quantities"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="定量描述主键ID"
    )

    __table_args__ = (
        Index("idx_bridge_quantities_code", "code"),
        Index("idx_bridge_quantities_active", "is_active"),
    )
