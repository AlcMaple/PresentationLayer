from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoriesCreate(BaseModel):
    """分类创建模型"""

    name: str = Field(..., max_length=100, description="分类名称")
    code: Optional[str] = Field(None, max_length=20, description="分类编码")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    # level: int = Field(0, description="层级深度")
    # sort_order: int = Field(0, description="排序序号")
    # is_active: bool = Field(True, description="是否启用")


class CategoriesUpdate(BaseModel):
    """分类更新模型"""

    name: Optional[str] = Field(None, max_length=100, description="分类名称")
    code: Optional[str] = Field(None, max_length=20, description="分类编码")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    # level: Optional[int] = Field(None, description="层级深度")
    # sort_order: Optional[int] = Field(None, description="排序序号")
    # is_active: Optional[bool] = Field(None, description="是否启用")


class CategoriesResponse(BaseModel):
    """分类响应模型"""

    id: int
    name: str
    code: Optional[str]
    description: Optional[str]
    level: int
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
