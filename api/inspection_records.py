from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from config.database import get_db
from services.inspection_records import get_inspection_records_service
from schemas.inspection_records import (
    InspectionRecordsCreate,
    InspectionRecordsUpdate,
    PathValidationRequest,
)
from utils.responses import success, bad_request
from exceptions import ValidationException, NotFoundException
from services.base_crud import PageParams

router = APIRouter(prefix="/inspection_records", tags=["检测记录管理"])


@router.post("/scales-by-damage", summary="根据病害类型获取标度选项")
async def get_scales_by_damage_type(
    path_request: PathValidationRequest,
    damage_type_code: str = Query(..., description="病害类型编码"),
    session: Session = Depends(get_db),
):
    """根据路径和病害类型获取对应的标度选项"""
    try:
        service = get_inspection_records_service(session)
        scales = service.get_scales_by_damage_type(path_request, damage_type_code)

        return success(
            {"scales": [scale.model_dump() for scale in scales]}, "获取标度选项成功"
        )

    except Exception as e:
        return bad_request(f"获取标度选项失败: {str(e)}")


@router.post("/", summary="创建检测记录")
async def create_inspection_record(
    record_data: InspectionRecordsCreate, session: Session = Depends(get_db)
):
    """创建新的检测记录"""
    try:
        service = get_inspection_records_service(session)
        result = service.create(record_data)

        return success(result.model_dump(), "创建检测记录成功")

    except ValidationException as e:
        return bad_request(str(e))
    except Exception as e:
        return bad_request(f"创建检测记录失败: {str(e)}")


@router.get("/{record_id}", summary="获取检测记录详情")
async def get_inspection_record(record_id: int, session: Session = Depends(get_db)):
    """根据ID获取检测记录详情"""
    try:
        service = get_inspection_records_service(session)
        result = service.get_record_with_details(record_id)

        return success(result.model_dump(), "获取检测记录详情成功")

    except NotFoundException as e:
        return bad_request(str(e))
    except Exception as e:
        return bad_request(f"获取检测记录详情失败: {str(e)}")


@router.put("/{record_id}", summary="更新检测记录")
async def update_inspection_record(
    record_id: int,
    update_data: InspectionRecordsUpdate,
    session: Session = Depends(get_db),
):
    """更新检测记录的可编辑字段"""
    try:
        service = get_inspection_records_service(session)
        result = service.update(record_id, update_data)

        return success(result.model_dump(), "更新检测记录成功")

    except (NotFoundException, ValidationException) as e:
        return bad_request(str(e))
    except Exception as e:
        return bad_request(f"更新检测记录失败: {str(e)}")


@router.delete("/{record_id}", summary="删除检测记录")
async def delete_inspection_record(record_id: int, session: Session = Depends(get_db)):
    """删除检测记录（软删除）"""
    try:
        service = get_inspection_records_service(session)
        success_flag = service.delete(record_id, cascade=False)

        if not success_flag:
            raise NotFoundException(
                resource="InspectionRecords", identifier=str(record_id)
            )

        return success(None, "删除检测记录成功")

    except NotFoundException as e:
        return bad_request(str(e))
    except Exception as e:
        return bad_request(f"删除检测记录失败: {str(e)}")


@router.get("/", summary="分页查询检测记录")
async def get_inspection_records_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: Session = Depends(get_db),
):
    """分页查询检测记录列表，支持按路径和病害类型筛选"""
    try:
        service = get_inspection_records_service(session)
        page_params = PageParams(page=page, size=size)

        # 构建基础查询过滤条件
        filters = {}
        items, total = service.get_list(page_params, filters)

        # 转换为响应格式
        detailed_items = []
        for item in items:
            try:
                detailed_item = service.get_record_with_details(item.id)
                detailed_items.append(detailed_item.model_dump())
            except:
                continue

        response_data = {
            "items": detailed_items,
            "total": total,
            "page": page,
            "size": size,
        }

        return success(response_data, "查询检测记录列表成功")

    except Exception as e:
        return bad_request(f"查询检测记录列表失败: {str(e)}")
