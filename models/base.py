from datetime import datetime
from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="更新时间"
    )


class Config:
    """SQLModel 配置"""

    from_attributes = True
    # JSON序列化使用枚举值
    use_enum_values = True
