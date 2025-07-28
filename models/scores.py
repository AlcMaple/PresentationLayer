from sqlmodel import Field, Index, Text
from typing import Optional
from decimal import Decimal

from .base import BaseModel


class Scores(BaseModel, table=True):
    """评分表"""

    __tablename__ = "scores"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="评分记录主键ID"
    )

    # 路径表
    category_id: int = Field(foreign_key="categories.id", description="桥梁类别ID")
    assessment_unit_id: Optional[int] = Field(
        default=None, foreign_key="assessment_units.id", description="评定单元ID"
    )
    bridge_type_id: int = Field(foreign_key="bridge_types.id", description="桥梁类型ID")
    part_id: int = Field(foreign_key="bridge_parts.id", description="部位ID")
    component_type_id: int = Field(
        foreign_key="bridge_component_types.id", description="部件类型ID"
    )

    # 权重和构件数量
    weight: Optional[Decimal] = Field(
        default=None, description="权重", max_digits=10, decimal_places=2
    )
    component_count: int = Field(default=0, description="构件数量")
    custom_component_count: Optional[int] = Field(
        default=None, description="自定义构件数量"
    )
    adjusted_weight: Optional[Decimal] = Field(
        default=None, description="调整后权重", max_digits=10, decimal_places=4
    )

    # 评分相关字段
    component_score: Optional[Decimal] = Field(
        default=None, description="部件评分", max_digits=5, decimal_places=2
    )
    part_score: Optional[Decimal] = Field(
        default=None, description="部位评分", max_digits=5, decimal_places=2
    )
    part_weight: Optional[Decimal] = Field(
        default=None, description="部位权重", max_digits=10, decimal_places=1
    )
    total_score: Optional[Decimal] = Field(
        default=None, description="总体评分", max_digits=5, decimal_places=2
    )
    evaluation_grade: Optional[str] = Field(
        default=None, description="评定等级", max_length=20
    )

    # 计算配置字段
    use_custom_count: bool = Field(
        default=False, description="是否使用自定义构件数量计算权重"
    )

    # 桥梁名称
    bridge_name: Optional[str] = Field(
        default=None, description="桥梁名称", max_length=200
    )

    # 状态字段
    is_active: bool = Field(description="是否启用", default=True)

    __table_args__ = (
        Index("idx_scores_category", "category_id"),
        Index("idx_scores_bridge_type", "bridge_type_id"),
        Index("idx_scores_part", "part_id"),
        Index("idx_scores_component_type", "component_type_id"),
        Index("idx_scores_active", "is_active"),
        # 按桥梁分组
        Index(
            "idx_scores_project",
            "category_id",
            "assessment_unit_id",
            "bridge_type_id",
        ),
        # 完整路径索引
        Index(
            "idx_scores_full_path",
            "category_id",
            "assessment_unit_id",
            "bridge_type_id",
            "part_id",
            "component_type_id",
        ),
    )
