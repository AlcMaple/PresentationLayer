from sqlmodel import Field, Index
from typing import Optional
from decimal import Decimal

from .base import BaseModel


class WeightReferences(BaseModel, table=True):
    """权重参考表"""

    __tablename__ = "weight_references"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="权重参考主键ID"
    )

    # 路径相关字段
    bridge_type_id: int = Field(foreign_key="bridge_types.id", description="桥梁类型ID")
    part_id: int = Field(foreign_key="bridge_parts.id", description="部位ID")
    component_type_id: int = Field(
        foreign_key="bridge_component_types.id", description="部件类型ID"
    )

    # 权重值
    weight: Decimal = Field(description="权重值", max_digits=10, decimal_places=2)

    # 备注信息
    remarks: Optional[str] = Field(default=None, description="备注", max_length=500)

    # 状态字段
    is_active: bool = Field(description="是否启用", default=True)

    __table_args__ = (
        Index("idx_weight_references_bridge_type", "bridge_type_id"),
        Index("idx_weight_references_part", "part_id"),
        Index("idx_weight_references_component_type", "component_type_id"),
        Index("idx_weight_references_active", "is_active"),
        # 按桥梁类型和部位查询
        Index(
            "idx_weight_references_bridge_part",
            "bridge_type_id",
            "part_id",
        ),
        # 唯一索引
        Index(
            "idx_weight_references_unique",
            "bridge_type_id",
            "part_id",
            "component_type_id",
            "is_active",
            unique=True,
        ),
    )
