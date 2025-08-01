from sqlmodel import Field, Index
from typing import Optional

from .base import BaseModel


class UserPaths(BaseModel, table=True):
    """用户自定义的桥梁实例路径表"""

    __tablename__ = "user_paths"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="用户路径主键ID"
    )
    user_id: Optional[int] = Field(
        default=None, description="创建该路径的用户ID, 为空时代表管理员创建的公共路径"
    )
    bridge_instance_name: str = Field(
        max_length=200, description="用户定义的实例名称, 例如: G65高速K123特大桥"
    )
    assessment_unit_instance_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="用户定义的评定单元实例名称, 例如: 主跨上部结构",
    )

    # 基础路径字段
    category_id: int = Field(foreign_key="categories.id", description="桥梁类别ID")
    assessment_unit_id: Optional[int] = Field(
        default=None, foreign_key="assessment_units.id", description="评定单元ID"
    )
    bridge_type_id: int = Field(foreign_key="bridge_types.id", description="桥梁类型ID")
    part_id: int = Field(foreign_key="bridge_parts.id", description="部位ID")
    structure_id: Optional[int] = Field(
        default=None, foreign_key="bridge_structures.id", description="结构类型ID"
    )
    component_type_id: Optional[int] = Field(
        default=None, foreign_key="bridge_component_types.id", description="部件类型ID"
    )
    component_form_id: Optional[int] = Field(
        default=None, foreign_key="bridge_component_forms.id", description="构件形式ID"
    )

    # 关联的基础路径ID
    paths_id: int = Field(foreign_key="paths.id", description="关联的基础路径ID")

    # 状态字段
    is_active: bool = Field(default=True, description="是否启用")

    __table_args__ = (
        Index("idx_user_paths_user_id", "user_id"),
        Index("idx_user_paths_user_active", "user_id", "is_active"),
        Index("idx_user_paths_instance_name", "instance_name"),
        Index("idx_user_paths_paths_id", "paths_id"),
        Index("idx_user_paths_active", "is_active"),
        # 业务查询索引
        Index("idx_user_paths_category_bridge", "category_id", "bridge_type_id"),
        Index("idx_user_paths_full_path", "category_id", "bridge_type_id", "part_id"),
    )
