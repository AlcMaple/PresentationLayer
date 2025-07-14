from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from config.database import get_db
from services.base_crud import BaseCRUDService, PageParams
from models import BridgeDiseases
from schemas.base import (
    Create,
    Update,
    Response,
)
from utils.responses import success
from exceptions import NotFoundException

router = APIRouter(prefix="/bridge_diseases", tags=["病害类型管理"])


@router.get("/", summary="分页查询病害类型列表")
async def get_bridge_diseases_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="病害类型名称模糊查询"),
    session: Session = Depends(get_db),
):
    """分页查询病害类型列表"""
    service = BaseCRUDService(BridgeDiseases, session)
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


@router.post("/", summary="创建病害类型")
async def create_bridge_diseases(
    category_data: Create, session: Session = Depends(get_db)
):
    """创建病害类型"""
    service = BaseCRUDService(BridgeDiseases, session)
    item = service.create(category_data)

    response_item = Response.model_validate(item)
    return success(response_item.model_dump(), "创建成功")


@router.put("/{id}", summary="更新病害类型")
async def update_bridge_diseases(
    id: int, category_data: Update, session: Session = Depends(get_db)
):
    """更新病害类型"""
    service = BaseCRUDService(BridgeDiseases, session)
    item = service.update(id, category_data)

    if not item:
        raise NotFoundException(resource="BridgeDiseases", identifier=str(id))

    response_item = Response.model_validate(item)
    return success(response_item.model_dump(), "更新成功")


@router.delete("/{id}", summary="删除病害类型")
async def delete_bridge_diseases(id: int, session: Session = Depends(get_db)):
    """删除病害类型"""
    service = BaseCRUDService(BridgeDiseases, session)
    success_flag = service.delete(id)

    if not success_flag:
        raise NotFoundException(resource="BridgeDiseases", identifier=str(id))

    return success(None, "删除成功")
