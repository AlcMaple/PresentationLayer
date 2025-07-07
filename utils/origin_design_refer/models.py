# models.py - 简化版本（去掉中间关系表）
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# 枚举类型
class DescriptionType(str, Enum):
    QUALITATIVE = "qualitative"  # 完性描述
    QUANTITATIVE = "quantitative"  # 定量描述


# =============================================================================
# 基础枚举表
# =============================================================================


class BridgeType(SQLModel, table=True):
    """桥类型表"""

    __tablename__ = "bridge_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Part(SQLModel, table=True):
    """部位表"""

    __tablename__ = "parts"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StructureType(SQLModel, table=True):
    """结构类型表"""

    __tablename__ = "structure_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    part_id: int = Field(foreign_key="parts.id")  # 部位→结构类型 (1:多)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ComponentType(SQLModel, table=True):
    """部件类型表"""

    __tablename__ = "component_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    structure_type_id: int = Field(
        foreign_key="structure_types.id"
    )  # 结构类型→部件类型 (1:多)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DamageType(SQLModel, table=True):
    """病害类型表"""

    __tablename__ = "damage_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Scale(SQLModel, table=True):
    """标度表"""

    __tablename__ = "scales"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name: str = Field(max_length=100)
    scale_value: str = Field(max_length=50)
    qualitative_description: Optional[str] = Field(
        default=None, max_length=1000
    )  # 完性描述
    quantitative_description: Optional[str] = Field(
        default=None, max_length=1000
    )  # 定量描述
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# 核心路径表
# =============================================================================


class BridgeDamageScalePath(SQLModel, table=True):
    """完整路径记录表：桥类型→部位→结构类型→部件类型→病害类型→标度"""

    __tablename__ = "bridge_damage_scale_paths"

    id: Optional[int] = Field(default=None, primary_key=True)
    bridge_type_id: int = Field(foreign_key="bridge_types.id")
    part_id: int = Field(foreign_key="parts.id")
    structure_type_id: int = Field(foreign_key="structure_types.id")
    component_type_id: int = Field(foreign_key="component_types.id")
    damage_type_id: int = Field(foreign_key="damage_types.id")
    scale_id: int = Field(foreign_key="scales.id")
    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# =============================================================================
# 响应模型
# =============================================================================


class BridgeTypeResponse(SQLModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int


class PartResponse(SQLModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int


class StructureTypeResponse(SQLModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    part_id: int
    part_name: str
    is_active: bool
    sort_order: int


class ComponentTypeResponse(SQLModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    structure_type_id: int
    structure_type_name: str
    is_active: bool
    sort_order: int


class DamageTypeResponse(SQLModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool
    sort_order: int


class ScaleResponse(SQLModel):
    id: int
    code: str
    name: str
    scale_value: str
    qualitative_description: Optional[str] = None
    quantitative_description: Optional[str] = None
    is_active: bool
    sort_order: int


class PathResponse(SQLModel):
    """路径响应模型"""

    id: int
    bridge_type_name: str
    part_name: str
    structure_type_name: str
    component_type_name: str
    damage_type_name: str
    scale_name: str
    scale_value: str
    qualitative_description: Optional[str] = None
    quantitative_description: Optional[str] = None
    sort_order: int
    is_active: bool


class PathStructureResponse(SQLModel):
    """路径结构响应"""

    bridge_type_id: int
    bridge_type_name: str
    part_id: int
    part_name: str
    structure_type_id: int
    structure_type_name: str
    component_type_id: int
    component_type_name: str
    damage_type_id: int
    damage_type_name: str
    scales: List[ScaleResponse]


# =============================================================================
# 创建/更新模型
# =============================================================================


class BridgeTypeCreate(SQLModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    sort_order: int = 0


class BridgeTypeUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PartCreate(SQLModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    sort_order: int = 0


class PartUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class StructureTypeCreate(SQLModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    part_id: int
    sort_order: int = 0


class StructureTypeUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    part_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ComponentTypeCreate(SQLModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    structure_type_id: int
    sort_order: int = 0


class ComponentTypeUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    structure_type_id: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class DamageTypeCreate(SQLModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    sort_order: int = 0


class DamageTypeUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ScaleCreate(SQLModel):
    code: str = Field(max_length=50)
    name: str = Field(max_length=100)
    scale_value: str = Field(max_length=50)
    qualitative_description: Optional[str] = None
    quantitative_description: Optional[str] = None
    sort_order: int = 0


class ScaleUpdate(SQLModel):
    code: Optional[str] = None
    name: Optional[str] = None
    scale_value: Optional[str] = None
    qualitative_description: Optional[str] = None
    quantitative_description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PathCreate(SQLModel):
    """创建路径"""

    bridge_type_id: int
    part_id: int
    structure_type_id: int
    component_type_id: int
    damage_type_id: int
    scale_ids: List[int]  # 支持批量添加标度


# =============================================================================
# 批量导入模型
# =============================================================================


class BatchImportItem(SQLModel):
    """批量导入的单条数据"""

    bridge_type: str  # 桥类型名称
    part: str  # 部位名称
    structure_type: Optional[str] = None  # 结构类型名称（可空）
    component_type: Optional[str] = None  # 部件类型名称（可空）
    damage_type: str  # 病害类型名称
    scales: List[str]  # 标度名称列表

    # 可选的描述信息
    bridge_type_desc: Optional[str] = None
    part_desc: Optional[str] = None
    structure_type_desc: Optional[str] = None
    component_type_desc: Optional[str] = None
    damage_type_desc: Optional[str] = None


class BatchImportRequest(SQLModel):
    """批量导入请求"""

    data: List[BatchImportItem]
    options: Optional[Dict[str, Any]] = {
        "skip_existing": True,  # 跳过已存在的数据
        "create_missing": True,  # 自动创建缺失的基础数据
        "validate_only": False,  # 只验证不实际导入
    }


class BatchImportResult(SQLModel):
    """批量导入结果"""

    success: bool
    total_items: int
    created_paths: int
    created_base_data: Dict[str, int]
    skipped_items: int
    errors: List[Dict[str, str]]
    warnings: List[str]
