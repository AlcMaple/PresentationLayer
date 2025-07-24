from sqlmodel import Field, Index, Text
from typing import Optional

from .base import BaseModel


class InspectionRecords(BaseModel, table=True):
    """检查记录表"""

    __tablename__ = "inspection_records"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="检查记录主键ID"
    )

    # 前7层路径字段
    category_id: int = Field(foreign_key="categories.id", description="桥梁类别ID")
    assessment_unit_id: Optional[int] = Field(
        default=None, foreign_key="assessment_units.id", description="评定单元ID"
    )
    bridge_type_id: int = Field(foreign_key="bridge_types.id", description="桥梁类型ID")
    part_id: int = Field(foreign_key="bridge_parts.id", description="部位ID")
    structure_id: Optional[int] = Field(
        default=None, foreign_key="bridge_structures.id", description="结构类型ID"
    )
    component_type_id: int = Field(
        foreign_key="bridge_component_types.id", description="部件类型ID"
    )
    component_form_id: int = Field(
        foreign_key="bridge_component_forms.id", description="构件形式ID"
    )

    # 病害和标度数据
    damage_type_id: int = Field(
        foreign_key="bridge_diseases.id", description="病害类型ID"
    )
    scale_id: int = Field(foreign_key="bridge_scales.id", description="标度ID")

    # 检查数据字段
    damage_location: Optional[str] = Field(
        description="病害位置", default=None, sa_type=Text
    )
    damage_description: Optional[str] = Field(
        description="病害描述", default=None, sa_type=Text
    )

    # 图片相关字段
    image_url: Optional[str] = Field(
        description="图片URL", default=None, max_length=500
    )

    # 构件名称字段
    component_name: Optional[str] = Field(
        description="构件名称", default=None, max_length=100
    )

    # 状态字段
    is_active: bool = Field(description="是否启用", default=True)

    __table_args__ = (
        Index("idx_inspection_records_category", "category_id"),
        Index("idx_inspection_records_bridge_type", "bridge_type_id"),
        Index("idx_inspection_records_part", "part_id"),
        Index("idx_inspection_records_component_type", "component_type_id"),
        Index("idx_inspection_records_component_form", "component_form_id"),
        Index("idx_inspection_records_damage_type", "damage_type_id"),
        Index("idx_inspection_records_scale", "scale_id"),
        Index("idx_inspection_records_active", "is_active"),
        # 复合索引
        Index(
            "idx_inspection_records_bridge_path",
            "part_id",
            "component_type_id",
        ),
        Index(
            "idx_inspection_records_path_damage",
            "category_id",
            "bridge_type_id",
            "part_id",
            "component_type_id",
            "damage_type_id",
        ),
        # 桥梁完整路径索引
        Index(
            "idx_inspection_records_full_path",
            "category_id",
            "bridge_type_id",
            "part_id",
            "component_type_id",
            "component_form_id",
        ),
        # 病害标度组合索引
        Index(
            "idx_inspection_records_damage_scale",
            "damage_type_id",
            "scale_id",
        ),
    )
