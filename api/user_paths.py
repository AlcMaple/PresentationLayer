from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from config.database import get_db
from services.user_paths import get_user_paths_service
from schemas.user_paths import CascadeOptionsRequest, UserPathsCreate, UserPathsUpdate
from utils.responses import success, bad_request
from utils.base import get_assessment_units_by_category

router = APIRouter(prefix="/user_paths", tags=["用户路径管理"])


@router.get("/cascade-options", summary="获取级联下拉选项")
async def get_cascade_options(
    bridge_type_id: Optional[int] = Query(None, description="桥梁类型ID"),
    part_id: Optional[int] = Query(None, description="部位ID"),
    structure_id: Optional[int] = Query(None, description="结构类型ID"),
    component_type_id: Optional[int] = Query(None, description="部件类型ID"),
    component_form_id: Optional[int] = Query(None, description="构件形式ID"),
    session: Session = Depends(get_db),
):
    """获取级联下拉选项"""
    service = get_user_paths_service(session)

    request = CascadeOptionsRequest(
        bridge_type_id=bridge_type_id,
        part_id=part_id,
        structure_id=structure_id,
        component_type_id=component_type_id,
        component_form_id=component_form_id,
    )

    options = service.get_cascade_options(request)

    return success(options.model_dump(), "获取级联选项成功")


@router.post("", summary="创建用户路径")
async def create_user_path(
    user_path_data: UserPathsCreate,
    session: Session = Depends(get_db),
):
    """创建用户路径"""
    service = get_user_paths_service(session)
    result = service.create(user_path_data)

    return success(result.model_dump(), "创建用户路径成功")


@router.get("/get-assessment_units", summary="获取评定单元")
async def get_assessment_units(
    category_id: int,
    session: Session = Depends(get_db),
):
    """获取评定单元"""
    units = get_assessment_units_by_category(category_id, session)
    return success(units, "获取评定单元成功")


@router.put("/{user_path_id}", summary="更新用户路径")
async def update_user_path(
    user_path_id: int,
    user_path_data: UserPathsUpdate,
    session: Session = Depends(get_db),
):
    """更新用户路径"""
    service = get_user_paths_service(session)
    result = service.update(user_path_id, user_path_data)

    return success(result.model_dump(), "更新用户路径成功")


@router.delete("/{user_path_id}", summary="删除用户路径")
async def delete_user_path(
    user_path_id: int,
    session: Session = Depends(get_db),
):
    """删除用户路径"""
    service = get_user_paths_service(session)
    result = service.delete(user_path_id)

    return success(result, "删除用户路径成功")
