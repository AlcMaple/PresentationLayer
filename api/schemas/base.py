from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Create(BaseModel):
    """创建模型"""

    name: str = Field(..., max_length=100, description="名称")
    code: Optional[str] = Field(None, max_length=20, description="编码")
    description: Optional[str] = Field(None, max_length=500, description="描述")


class Update(BaseModel):
    """更新模型"""

    name: Optional[str] = Field(None, max_length=100, description="名称")
    code: Optional[str] = Field(None, max_length=20, description="编码")
    description: Optional[str] = Field(None, max_length=500, description="描述")


class Response(BaseModel):
    """响应模型"""

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
