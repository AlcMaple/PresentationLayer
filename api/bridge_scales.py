from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from config.database import get_db
from services.base_crud import PageParams
from models.enums import ScalesType
from schemas.bridge_scales import (
    BridgeScalesCreate,
    BridgeScalesUpdate,
    BridgeScalesResponse,
)
from utils.responses import success
from services.bridge_scales import get_bridge_scales_service

router = APIRouter(prefix="/bridge_scales", tags=["标度管理"])


@router.get("/", summary="分页查询标度列表")
async def get_bridge_scales_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="标度名称模糊查询"),
    scale_type: Optional[ScalesType] = Query(
        None,
        description="标度类型筛选（NUMERIC(数值)/RANGE(范围)/TEXT(文本)）",
    ),
    scale_value: Optional[int] = Query(None, description="标度值"),
    min_value: Optional[int] = Query(None, description="范围最小值"),
    max_value: Optional[int] = Query(None, description="范围最大值"),
    unit: Optional[str] = Query(None, description="单位"),
    display_text: Optional[str] = Query(None, description="显示文本模糊查询"),
    session: Session = Depends(get_db),
):
    """分页查询标度列表"""
    # 创建服务实例
    service = get_bridge_scales_service(session)
    
    # 分页参数
    page_params = PageParams(page=page, size=size)
    
    # 查询数据
    items, total = service.get_list_with_filters(
        page_params=page_params,
        name=name,
        scale_type=scale_type,
        scale_value=scale_value,
        min_value=min_value,
        max_value=max_value,
        unit=unit,
        display_text=display_text,
    )
    
    # 转换响应格式
    list_items = [
        BridgeScalesResponse.model_validate(item).model_dump() for item in items
    ]
    
    response_item = {
        "items": list_items,
        "total": total,
        "page": page,
        "size": size,
    }
    return success(response_item, "查询成功")


@router.post("/", summary="创建标度")
async def create_bridge_scales(
    scale_data: BridgeScalesCreate, session: Session = Depends(get_db)
):
    """创建标度"""
    # 创建服务实例
    service = get_bridge_scales_service(session)
    
    # 创建标度
    db_obj = service.create(scale_data)
    
    # 转换响应格式
    response_item = BridgeScalesResponse.model_validate(db_obj)
    return success(response_item.model_dump(), "创建成功")


# @router.delete("/{id}", summary="删除标度")
# async def delete_bridge_scales(id: int, session: Session = Depends(get_db)):
#     """删除标度"""
#     # 创建服务实例
#     service = get_bridge_scales_service(session)
    
#     # 删除标度
#     service.delete(id)
    
#     return success(None, "删除成功")


@router.put("/{id}", summary="更新标度")
async def update_bridge_scales(
    id: int, scale_data: BridgeScalesUpdate, session: Session = Depends(get_db)
):
    """更新标度"""
    # 创建服务实例
    service = get_bridge_scales_service(session)
    
    # 更新标度
    db_obj = service.update(id, scale_data)
    
    # 转换响应格式
    response_item = BridgeScalesResponse.model_validate(db_obj)
    return success(response_item.model_dump(), "更新成功")
