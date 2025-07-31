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
    instance_name: str = Field(
        max_length=200, description="用户定义的实例名称, 例如: G65高速K123特大桥"
    )
    assessment_unit_instance_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="用户定义的评定单元实例名称, 例如: 主跨上部结构",
    )

    # 关联到 Paths 表的外键
    category_id: int = Field(default=None, foreign_key="categories.id")
    assessment_unit_id: Optional[int] = Field(
        default=None, foreign_key="assessment_units.id"
    )
    bridge_type_id: int = Field(default=None, foreign_key="bridge_types.id")
    part_id: int = Field(default=None, foreign_key="bridge_parts.id")
    structure_id: Optional[int] = Field(
        default=None, foreign_key="bridge_structures.id"
    )
    component_type_id: Optional[int] = Field(
        default=None, foreign_key="bridge_component_types.id"
    )
    component_form_id: Optional[int] = Field(
        default=None, foreign_key="bridge_component_forms.id"
    )
    disease_id: int = Field(default=None, foreign_key="bridge_diseases.id")
    scale_id: int = Field(default=None, foreign_key="bridge_scales.id")
    quality_id: int = Field(default=None, foreign_key="bridge_qualities.id")
    quantity_id: int = Field(default=None, foreign_key="bridge_quantities.id")

    # 这个 paths_id 指向 Paths 表中的某一条完整记录
    paths_id: int = Field(
        default=None, foreign_key="paths.id", description="关联的基础路径ID"
    )

    # 状态
    is_active: bool = Field(default=True, description="是否启用")

    # --- 索引配置 ---
    __table_args__ = (
        Index("idx_user_paths_user_id", "user_id"),
        Index(
            "idx_user_paths_user_active", "user_id", "is_active"
        ),  # 查询特定用户的有效路径
        Index("idx_user_paths_instance_name", "instance_name"),  # 按实例名称搜索
    )
