from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        """偏移量"""
        return (self.page - 1) * self.size
