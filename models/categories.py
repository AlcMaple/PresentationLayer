from sqlmodel import Field, Index
from typing import Optional

from .base import BaseModel


class CategoriesBase(BaseModel):
    """分类基础模型"""

    name: str = Field(max_length=100, description="分类名称")
    code: str = Field(max_length=50, description="分类编码", unique=True)
    description: Optional[str] = Field(
        default=None, max_length=500, description="分类描述"
    )
    parent_id: Optional[int] = Field(default=None, description="父级分类ID")
    level: int = Field(default=0, description="层级深度")
    sort_order: int = Field(default=0, description="排序序号")
    is_active: bool = Field(default=True, description="是否启用")


class Categories(CategoriesBase, table=True):
    """分类表"""

    __tablename__ = "categories"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="分类主键ID"
    )  # 主键自增

    # 外键约束
    parent_id: Optional[int] = Field(
        default=None, foreign_key="categories.id", description="父级分类ID"
    )

    # 索引配置
    __table_args__ = (
        Index("idx_categories_parent_id", "parent_id"),
        Index("idx_categories_code", "code"),
        Index("idx_categories_level", "level"),
        Index("idx_categories_active", "is_active"),
    )
