from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

from .base import BaseModel

# 分类基础信息表
class CategoriesBase(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    level: int = Field(default=0)
    

# 分类表
class Categories(CategoriesBase, table=True):
    __tablename__ = "categories"