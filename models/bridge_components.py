from sqlmodel import SQLModel, Field, Index, Text
from typing import Optional
from sqlalchemy import text

from .base import BaseModel
from .enums import ScalesType


class BridgeComponentBase(BaseModel):
    name: str = Field(description="名称", sa_type=Text)
    code: Optional[str] = Field(
        description="编码", default=None, max_length=20, index=True
    )
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
    level: int = Field(description="层级深度", default=2)

    __table_args__ = (
        Index("idx_bridge_types_code", "code"),
        Index("idx_bridge_types_active", "is_active"),
        Index("idx_bridge_types_name", text("name(255)")),
        Index("idx_bridge_types_level", "level"),
    )


# 部位表
class BridgeParts(BridgeComponentBase, table=True):
    __tablename__ = "bridge_parts"

    id: Optional[int] = Field(default=None, primary_key=True, description="部位主键ID")
    level: int = Field(description="层级深度", default=3)

    __table_args__ = (
        Index("idx_bridge_parts_code", "code"),
        Index("idx_bridge_parts_active", "is_active"),
        Index("idx_bridge_parts_name", text("name(255)")),
        Index("idx_bridge_parts_level", "level"),
    )


# 结构类型表
class BridgeStructures(BridgeComponentBase, table=True):
    __tablename__ = "bridge_structures"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="结构类型主键ID"
    )
    level: int = Field(description="层级深度", default=4)

    __table_args__ = (
        Index("idx_bridge_structures_code", "code"),
        Index("idx_bridge_structures_active", "is_active"),
        Index("idx_bridge_structures_name", text("name(255)")),
        Index("idx_bridge_structures_level", "level"),
    )


# 部件类型表
class BridgeComponentTypes(BridgeComponentBase, table=True):
    __tablename__ = "bridge_component_types"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="部件类型主键ID"
    )
    level: int = Field(description="层级深度", default=5)

    __table_args__ = (
        Index("idx_bridge_component_types_code", "code"),
        Index("idx_bridge_component_types_active", "is_active"),
        Index("idx_bridge_component_types_name", text("name(255)")),
        Index("idx_bridge_component_types_level", "level"),
    )


# 构件形式表
class BridgeComponentForms(BridgeComponentBase, table=True):
    __tablename__ = "bridge_component_forms"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="构件形式主键ID"
    )
    level: int = Field(description="层级深度", default=6)

    __table_args__ = (
        Index("idx_bridge_component_forms_code", "code"),
        Index("idx_bridge_component_forms_active", "is_active"),
        Index("idx_bridge_component_forms_name", text("name(255)")),
        Index("idx_bridge_component_forms_level", "level"),
    )


# 病害类型表
class BridgeDiseases(BridgeComponentBase, table=True):
    __tablename__ = "bridge_diseases"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="病害类型主键ID"
    )
    level: int = Field(description="层级深度", default=7)

    __table_args__ = (
        Index("idx_bridge_diseases_code", "code"),
        Index("idx_bridge_diseases_active", "is_active"),
        Index("idx_bridge_diseases_name", text("name(255)")),
        Index("idx_bridge_diseases_level", "level"),
    )


# 标度表
class BridgeScales(BridgeComponentBase, table=True):
    __tablename__ = "bridge_scales"

    id: Optional[int] = Field(default=None, primary_key=True, description="标度主键ID")
    scale_type: ScalesType = Field(
        description="标度类型：NUMERIC(数值)/RANGE(范围)/TEXT(文本)"
    )
    scale_value: Optional[int] = Field(default=None, description="标度值")
    min_value: Optional[int] = Field(default=None, description="范围最小值")
    max_value: Optional[int] = Field(default=None, description="范围最大值")
    unit: Optional[str] = Field(default=None, description="单位")
    display_text: Optional[str] = Field(default=None, description="显示文本")
    level: int = Field(description="层级深度", default=8)

    __table_args__ = (
        Index("idx_bridge_scales_code", "code"),
        Index("idx_bridge_scales_active", "is_active"),
        Index("idx_bridge_scales_value", "scale_value"),
        Index("idx_bridge_scales_type", "scale_type"),
        Index("idx_bridge_scales_name", text("name(255)")),
        Index("idx_bridge_scales_level", "level"),
    )


# 定性描述表
class BridgeQualities(BridgeComponentBase, table=True):
    __tablename__ = "bridge_qualities"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="定性描述主键ID"
    )
    level: int = Field(description="层级深度", default=9)

    __table_args__ = (
        Index("idx_bridge_qualities_code", "code"),
        Index("idx_bridge_qualities_active", "is_active"),
        Index("idx_bridge_qualities_name", text("name(255)")),
        Index("idx_bridge_qualities_level", "level"),
    )


# 定量描述
class BridgeQuantities(BridgeComponentBase, table=True):
    __tablename__ = "bridge_quantities"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="定量描述主键ID"
    )
    level: int = Field(description="层级深度", default=10)

    __table_args__ = (
        Index("idx_bridge_quantities_code", "code"),
        Index("idx_bridge_quantities_active", "is_active"),
        Index("idx_bridge_quantities_name", text("name(255)")),
        Index("idx_bridge_quantities_level", "level"),
    )
