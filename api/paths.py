from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional
from fastapi.responses import StreamingResponse
from io import BytesIO
from datetime import datetime
import urllib.parse

from config.database import get_db
from services.paths import get_paths_service
from services.base_crud import PageParams
from schemas.paths import PathsCreate, PathsUpdate, PathConditions
from utils.responses import success, server_error
from exceptions import NotFoundException

router = APIRouter(prefix="/paths", tags=["路径管理"])


@router.get("/", summary="分页查询路径列表")
async def get_paths_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    # 按code过滤
    category_code: Optional[str] = Query(None, description="桥梁类别编码"),
    assessment_unit_code: Optional[str] = Query(None, description="评定单元编码"),
    bridge_type_code: Optional[str] = Query(None, description="桥梁类型编码"),
    part_code: Optional[str] = Query(None, description="部位编码"),
    structure_code: Optional[str] = Query(None, description="结构类型编码"),
    component_type_code: Optional[str] = Query(None, description="部件类型编码"),
    component_form_code: Optional[str] = Query(None, description="构件形式编码"),
    disease_code: Optional[str] = Query(None, description="病害类型编码"),
    scale_code: Optional[str] = Query(None, description="标度编码"),
    quality_code: Optional[str] = Query(None, description="定性描述编码"),
    quantity_code: Optional[str] = Query(None, description="定量描述编码"),
    session: Session = Depends(get_db),
):
    """分页查询路径列表"""
    service = get_paths_service(session)
    page_params = PageParams(page=page, size=size)

    # 查询条件
    conditions = PathConditions(
        category_code=category_code,
        assessment_unit_code=assessment_unit_code,
        bridge_type_code=bridge_type_code,
        part_code=part_code,
        structure_code=structure_code,
        component_type_code=component_type_code,
        component_form_code=component_form_code,
        disease_code=disease_code,
        scale_code=scale_code,
        quality_code=quality_code,
        quantity_code=quantity_code,
    )

    items, total = service.get_paths_with_pagination(page_params, conditions)

    response_data = {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }
    return success(response_data, "查询成功")


@router.get("/filter-options", summary="获取分页查询条件选项")
async def get_filter_options(session: Session = Depends(get_db)):
    """获取所有相关表的code和name选项"""
    service = get_paths_service(session)
    options = service.get_filter_options()
    return success(options, "获取分页查询条件选项成功")


@router.get("/options", summary="获取所有路径选项")
async def get_options(session: Session = Depends(get_db)):
    """获取所有路径选项"""
    service = get_paths_service(session)
    options = service.get_options()
    return success(options, "获取路径选项成功")


@router.post("/", summary="创建路径")
async def create_path(path_data: PathsCreate, session: Session = Depends(get_db)):
    """创建路径"""
    service = get_paths_service(session)
    item = service.create(path_data)
    # 获取包含关联数据的详细信息
    detailed_item = service.get_by_id_with_details(item.id)
    response_item = detailed_item.model_dump() if detailed_item else None
    return success(response_item, "创建成功")


@router.get("/export", summary="导出路径 Excel 模板")
async def export_path_template(session: Session = Depends(get_db)):
    """导出路径 Excel 模板"""
    try:
        service = get_paths_service(session)
        excel_bytes = service.export_template()
        buffer = BytesIO(excel_bytes)

        # 设置文件名
        filename = f"bridge_path_template.xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        return server_error(f"导出模板失败: {str(e)}")



@router.get("/{path_id}", summary="获取单个路径")
async def get_path(path_id: int, session: Session = Depends(get_db)):
    """根据ID获取单个路径"""
    service = get_paths_service(session)
    item = service.get_by_id_with_details(path_id)
    if not item:
        raise NotFoundException(resource="Paths", identifier=str(path_id))

    response_item = item.model_dump()
    return success(response_item, "查询成功")


@router.put("/{path_id}", summary="更新路径")
async def update_path(
    path_id: int, path_data: PathsUpdate, session: Session = Depends(get_db)
):
    """更新路径"""
    service = get_paths_service(session)
    item = service.update(path_id, path_data)
    # 获取包含关联数据的详细信息
    detailed_item = service.get_by_id_with_details(path_id)
    response_item = detailed_item.model_dump() if detailed_item else None
    return success(response_item, "更新成功")


@router.delete("/{path_id}", summary="删除路径")
async def delete_path(path_id: int, session: Session = Depends(get_db)):
    """删除路径"""
    service = get_paths_service(session)
    success_result = service.delete(path_id, cascade=False)
    return success(None, "删除成功")


@router.get("/by-code/{code}", summary="根据编码获取路径")
async def get_path_by_code(code: str, session: Session = Depends(get_db)):
    """根据编码获取路径"""
    service = get_paths_service(session)
    item = service.get_by_code(code)
    if not item:
        raise NotFoundException(resource="Paths", identifier=code)

    # 获取包含关联数据的详细信息
    detailed_item = service.get_by_id_with_details(item.id)
    response_item = detailed_item.model_dump() if detailed_item else None
    return success(response_item, "查询成功")
