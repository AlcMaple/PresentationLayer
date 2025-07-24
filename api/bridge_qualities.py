from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from config.database import get_db
from services.base_crud import get_base_crud_service, PageParams
from models import BridgeQualities
from schemas.base import (
    Create,
    Update,
    Response,
)
from utils.responses import success
from exceptions import NotFoundException

router = APIRouter(prefix="/bridge_qualities", tags=["定性描述管理"])


@router.get("/", summary="分页查询定性描述列表")
async def get_bridge_qualities_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="定性描述名称模糊查询"),
    session: Session = Depends(get_db),
):
    """分页查询定性描述列表"""
    service = get_base_crud_service(BridgeQualities, session)
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


@router.post("/", summary="创建定性描述")
async def create_bridge_qualities(
    category_data: Create, session: Session = Depends(get_db)
):
    """创建定性描述"""
    service = get_base_crud_service(BridgeQualities, session)
    item = service.create(category_data)

    response_item = Response.model_validate(item)
    return success(response_item.model_dump(), "创建成功")


@router.put("/{id}", summary="更新定性描述")
async def update_bridge_qualities(
    id: int, category_data: Update, session: Session = Depends(get_db)
):
    """更新定性描述"""
    service = get_base_crud_service(BridgeQualities, session)
    item = service.update(id, category_data)

    if not item:
        raise NotFoundException(resource="BridgeQualities", identifier=str(id))

    response_item = Response.model_validate(item)
    return success(response_item.model_dump(), "更新成功")


# @router.delete("/{id}", summary="删除定性描述")
# async def delete_bridge_qualities(id: int, session: Session = Depends(get_db)):
#     """删除定性描述"""
#     service = get_base_crud_service(BridgeQualities, session)
#     success_flag = service.delete(id)

#     if not success_flag:
#         raise NotFoundException(resource="BridgeQualities", identifier=str(id))

#     return success(None, "删除成功")
