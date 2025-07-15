from sqlmodel import Field, Index
from typing import Optional

from .base import BaseModel


class Paths(BaseModel, table=True):
    """桥梁数据路径表"""

    __tablename__ = "paths"

    id: Optional[int] = Field(default=None, primary_key=True, description="路径主键ID")
    code: str = Field(max_length=50, unique=True, description="路径编码")
    name: str = Field(max_length=200, description="路径名称")
    is_active: bool = Field(default=True, description="是否启用")

    # 层级路径字段
    category_id: Optional[int] = Field(
        default=None, foreign_key="categories.id", description="桥梁类别ID"
    )
    assessment_unit_id: Optional[int] = Field(
        default=None, foreign_key="assessment_units.id", description="评定单元ID"
    )
    bridge_type_id: Optional[int] = Field(
        default=None, foreign_key="bridge_types.id", description="桥梁类型ID"
    )
    part_id: Optional[int] = Field(
        default=None, foreign_key="bridge_parts.id", description="部位ID"
    )
    structure_id: Optional[int] = Field(
        default=None, foreign_key="bridge_structures.id", description="结构类型ID"
    )
    component_type_id: Optional[int] = Field(
        default=None, foreign_key="bridge_component_types.id", description="部件类型ID"
    )
    component_form_id: Optional[int] = Field(
        default=None, foreign_key="bridge_component_forms.id", description="构件形式ID"
    )
    disease_id: Optional[int] = Field(
        default=None, foreign_key="bridge_diseases.id", description="病害类型ID"
    )
    scale_id: Optional[int] = Field(
        default=None, foreign_key="bridge_scales.id", description="标度ID"
    )
    quality_id: Optional[int] = Field(
        default=None, foreign_key="bridge_qualities.id", description="定性描述ID"
    )
    quantity_id: Optional[int] = Field(
        default=None, foreign_key="bridge_quantities.id", description="定量描述ID"
    )

    # 索引配置
    __table_args__ = (
        # 单索引
        Index("idx_paths_category", "category_id"),
        Index("idx_paths_assessment_unit", "assessment_unit_id"),
        Index("idx_paths_bridge_type", "bridge_type_id"),
        Index("idx_paths_part", "part_id"),
        Index("idx_paths_structure", "structure_id"),
        Index("idx_paths_component_type", "component_type_id"),
        Index("idx_paths_component_form", "component_form_id"),
        Index("idx_paths_disease", "disease_id"),
        Index("idx_paths_scale", "scale_id"),
        Index("idx_paths_active", "is_active"),
        # 复合索引
        Index("idx_paths_category_unit", "category_id", "assessment_unit_id"),
        Index("idx_paths_category_bridge_type", "category_id", "bridge_type_id"),
        Index("idx_paths_unit_bridge_type", "assessment_unit_id", "bridge_type_id"),
        Index("idx_paths_bridge_disease", "bridge_type_id", "disease_id"),
        # 路径索引
        Index(
            "idx_paths_full_hierarchy_active",
            "is_active",
            "category_id",
            "assessment_unit_id",
            "bridge_type_id",
            "part_id",
            "structure_id",
            "component_type_id",
            "component_form_id",
            "disease_id",
        ),
    )
