from sqlmodel import Field, Index
from typing import Optional
from enum import Enum

from .base import BaseModel


class AssessmentUnit(BaseModel, table=True):
    """评定单元表"""

    __tablename__ = "assessment_units"

    id: Optional[int] = Field(
        default=None, primary_key=True, description="评定单元主键ID"
    )
    name: str = Field(description="评定单元名称")
    code: Optional[str] = Field(
        description="评定单元编码", default=None, max_length=20, index=True
    )
    description: Optional[str] = Field(description="评定单元描述", default=None)
    sort_order: int = Field(description="排序", default=0)
    level: int = Field(description="层级深度", default=1)
    is_active: bool = Field(description="是否启用", default=True)

    __table_args__ = (
        Index("idx_assessment_units_code", "code"),
        Index("idx_assessment_units_active", "is_active"),
        Index("idx_assessment_units_name", "name"),
        Index("idx_assessment_units_level", "level"),
    )
