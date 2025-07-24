from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from config.database import get_db
from services.base_crud import get_base_crud_service, PageParams
from models import BridgeComponentTypes
from schemas.base import (
    Create,
    Update,
    Response,
)
from utils.responses import success
from exceptions import NotFoundException

router = APIRouter(prefix="/bridge_component_types", tags=["部件类型管理"])


@router.get("/", summary="分页查询部件类型列表")
async def get_bridge_component_types_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="部件类型名称模糊查询"),
    session: Session = Depends(get_db),
):
    """分页查询部件类型列表"""
    service = get_base_crud_service(BridgeComponentTypes, session)
    page_params = PageParams(page=page, size=size)

    filters = {}
    if name:
        filters["name"] = name

    items, total = service.get_list(page_params, filters)

    list_items = [Response.model_validate(item).model_dump() for item in items]
    response_item = {
        "items": list_items,
        "total": total,
        "page": page,
        "size": size,
    }
    return success(response_item, "查询成功")


@router.post("/", summary="创建部件类型")
async def create_bridge_component_types(
    category_data: Create, session: Session = Depends(get_db)
):
    """创建部件类型"""
    service = get_base_crud_service(BridgeComponentTypes, session)
    item = service.create(category_data)

    response_item = Response.model_validate(item)
    return success(response_item.model_dump(), "创建成功")


@router.put("/{id}", summary="更新部件类型")
async def update_bridge_component_types(
    id: int, category_data: Update, session: Session = Depends(get_db)
):
    """更新部件类型"""
    service = get_base_crud_service(BridgeComponentTypes, session)
    item = service.update(id, category_data)

    if not item:
        raise NotFoundException(resource="BridgeComponentTypes", identifier=str(id))

    response_item = Response.model_validate(item)
    return success(response_item.model_dump(), "更新成功")


# @router.delete("/{id}", summary="删除部件类型")
# async def delete_bridge_component_types(id: int, session: Session = Depends(get_db)):
#     """删除部件类型"""
#     service = get_base_crud_service(BridgeComponentTypes, session)
#     success_flag = service.delete(id)

#     if not success_flag:
#         raise NotFoundException(resource="BridgeComponentTypes", identifier=str(id))

#     return success(None, "删除成功")
