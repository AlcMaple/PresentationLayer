from sqlmodel import Field, Index, Text
from typing import Optional

from .base import BaseModel


class InspectionRecords(BaseModel, table=True):
    """检查记录表"""

    __tablename__ = "inspection_records"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="检查记录主键ID"
    )

    # 用户ID字段
    user_id: Optional[int] = Field(
        default=None, description="创建该记录的用户ID, 为空时代表管理员创建"
    )

    # 前7层路径字段
    # 用户实例路径字段
    bridge_instance_name: Optional[str] = Field(
        default=None, max_length=200, description="桥梁实例名称"
    )
    assessment_unit_instance_name: Optional[str] = Field(
        default=None, max_length=200, description="评定单元实例名称"
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

    user_paths_id: Optional[int] = Field(
        default=None, foreign_key="user_paths.id", description="用户实例路径ID"
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
        # 用户ID索引
        Index("idx_inspection_records_user_id", "user_id"),
        Index("idx_inspection_records_user_active", "user_id", "is_active"),
        # 实例名称索引
        Index("idx_inspection_records_bridge_instance", "bridge_instance_name"),
        Index(
            "idx_inspection_records_assessment_instance",
            "assessment_unit_instance_name",
        ),
        Index(
            "idx_inspection_records_bridge_assessment",
            "bridge_instance_name",
            "assessment_unit_instance_name",
        ),
        # 基础路径索引
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
            "bridge_type_id",
            "part_id",
            "component_type_id",
            "damage_type_id",
        ),
        # 桥梁完整路径索引
        Index(
            "idx_inspection_records_full_path",
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
        # 实例路径完整索引
        Index(
            "idx_inspection_records_instance_full_path",
            "bridge_instance_name",
            "assessment_unit_instance_name",
            "bridge_type_id",
            "part_id",
            "component_type_id",
            "component_form_id",
        ),
    )
