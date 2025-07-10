from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from config.database import get_db
from services.base_crud import BaseCRUDService, PageParams
from models import Categories
from api.schemas.categories import (
    CategoriesCreate,
    CategoriesUpdate,
    CategoriesResponse,
)
from utils.responses import success
from exceptions import NotFoundException

router = APIRouter(prefix="/categories", tags=["分类管理"])


@router.get("/", summary="分页查询分类列表")
async def get_categories_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="分类名称模糊查询"),
    session: Session = Depends(get_db),
):
    """分页查询分类列表"""
    service = BaseCRUDService(Categories, session)
    page_params = PageParams(page=page, size=size)

    filters = {}
    if name:
        filters["name"] = name

    items, total = service.get_list(page_params, filters)

    list_items = [
        CategoriesResponse.model_validate(item).model_dump() for item in items
    ]
    response_item = {
        "items": list_items,
        "total": total,
        "page": page,
        "size": size,
    }
    return success(response_item, "查询成功")


@router.post("/", summary="创建分类")
async def create_category(
    category_data: CategoriesCreate, session: Session = Depends(get_db)
):
    """创建分类"""
    service = BaseCRUDService(Categories, session)
    item = service.create(category_data)

    response_item = CategoriesResponse.model_validate(item)
    return success(response_item.model_dump(), "创建成功")


@router.put("/{id}", summary="更新分类")
async def update_category(
    id: int, category_data: CategoriesUpdate, session: Session = Depends(get_db)
):
    """更新分类"""
    service = BaseCRUDService(Categories, session)
    item = service.update(id, category_data)

    if not item:
        raise NotFoundException(resource="Categories", identifier=str(id))

    response_item = CategoriesResponse.model_validate(item)
    return success(response_item.model_dump(), "更新成功")


@router.delete("/{id}", summary="删除分类")
async def delete_category(id: int, session: Session = Depends(get_db)):
    """删除分类"""
    service = BaseCRUDService(Categories, session)
    success_flag = service.delete(id)

    if not success_flag:
        raise NotFoundException(resource="Categories", identifier=str(id))

    return success(None, "删除成功")
