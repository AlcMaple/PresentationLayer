from pydantic import BaseModel, Field, ValidationError, model_validator, field_validator
from typing import Optional
from datetime import datetime
from models.enums import ScalesType


class BridgeScalesCreate(BaseModel):
    """标度创建模型"""

    name: str = Field(..., max_length=100, description="标度名称", example="")
    code: Optional[str] = Field(None, max_length=20, description="标度编码", example="")
    description: Optional[str] = Field(
        None, max_length=500, description="标度描述", example=""
    )
    scale_type: ScalesType = Field(
        ..., description="标度类型", example=ScalesType.NUMERIC
    )
    scale_value: Optional[int] = Field(None, description="标度值", example=1)
    min_value: Optional[int] = Field(None, description="范围最小值", example=0)
    max_value: Optional[int] = Field(None, description="范围最大值", example=10)
    unit: Optional[str] = Field(None, max_length=20, description="单位", example="mm")
    display_text: Optional[str] = Field(
        None, max_length=200, description="显示文本", example=""
    )

    @model_validator(mode="after")
    @classmethod
    def validate_scale_fields(cls, values):
        """根据标度类型验证必填字段"""
        scale_type = values.scale_type

        if scale_type == ScalesType.NUMERIC:
            # 数字型
            if values.scale_value is None:
                raise ValueError("数字型标度必须填写标度值(scale_value)")
        elif scale_type == ScalesType.RANGE:
            # 范围型
            if values.min_value is None:
                raise ValueError("范围型标度必须填写最小值(min_value)")
            if values.max_value is None:
                raise ValueError("范围型标度必须填写最大值(max_value)")
            if not values.unit or not values.unit.strip():
                raise ValueError("范围型标度必须填写单位(unit)")
            if values.min_value > values.max_value:
                raise ValueError("最小值不能大于最大值")
        elif scale_type == ScalesType.TEXT:
            # 文本型
            if not values.display_text or not values.display_text.strip():
                raise ValueError("文本型标度必须填写显示文本(display_text)")

        return values


class BridgeScalesUpdate(BaseModel):
    """标度更新模型"""

    name: Optional[str] = Field(
        None, max_length=100, description="标度名称", example=""
    )
    code: Optional[str] = Field(None, max_length=20, description="标度编码", example="")
    description: Optional[str] = Field(
        None, max_length=500, description="标度描述", example=""
    )
    scale_type: Optional[ScalesType] = Field(
        ..., description="标度类型", example=ScalesType.NUMERIC
    )
    scale_value: Optional[int] = Field(None, description="标度值", example=1)
    min_value: Optional[int] = Field(None, description="范围最小值", example=0)
    max_value: Optional[int] = Field(None, description="范围最大值", example=10)
    unit: Optional[str] = Field(None, max_length=20, description="单位", example="mm")
    display_text: Optional[str] = Field(
        None, max_length=200, description="显示文本", example=""
    )

    @model_validator(mode="after")
    @classmethod
    def validate_scale_fields(cls, values):
        """根据标度类型验证必填字段"""
        scale_type = values.scale_type

        if scale_type == ScalesType.NUMERIC:
            # 数字型
            if values.scale_value is None:
                raise ValueError("数字型标度必须填写标度值(scale_value)")
        elif scale_type == ScalesType.RANGE:
            # 范围型
            if values.min_value is None:
                raise ValueError("范围型标度必须填写最小值(min_value)")
            if values.max_value is None:
                raise ValueError("范围型标度必须填写最大值(max_value)")
            if not values.unit or not values.unit.strip():
                raise ValueError("范围型标度必须填写单位(unit)")
            if values.min_value > values.max_value:
                raise ValueError("最小值不能大于最大值")
        elif scale_type == ScalesType.TEXT:
            # 文本型
            if not values.display_text or not values.display_text.strip():
                raise ValueError("文本型标度必须填写显示文本(display_text)")

        return values


class BridgeScalesResponse(BaseModel):
    """标度响应模型"""

    id: int
    name: str
    code: Optional[str]
    description: Optional[str]
    scale_type: ScalesType
    scale_value: Optional[int]
    min_value: Optional[int]
    max_value: Optional[int]
    unit: Optional[str]
    display_text: Optional[str]
    level: int
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
