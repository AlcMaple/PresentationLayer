from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from config.database import get_db
from services.inspection_records import get_inspection_records_service
from schemas.inspection_records import (
    InspectionRecordsCreate,
    InspectionRecordsUpdate,
    PathValidationRequest,
    DamageReferenceRequest,
)
from utils.responses import success, bad_request
from exceptions import ValidationException, NotFoundException
from services.base_crud import PageParams

router = APIRouter(prefix="/inspection_records", tags=["检查记录管理"])


@router.post("/", summary="创建检查记录")
async def create_inspection_record(
    record_data: InspectionRecordsCreate, session: Session = Depends(get_db)
):
    """创建新的检查记录"""
    service = get_inspection_records_service(session)
    result = service.create(record_data)
    return success(result.model_dump(), "创建检查记录成功")


@router.post("/form-options", summary="根据路径获取表单选项")
async def get_form_options_by_path(
    path_request: PathValidationRequest,
    session: Session = Depends(get_db),
):
    """获取病害类型和对应的标度选项"""
    try:
        service = get_inspection_records_service(session)
        options = service.get_form_options_by_path(path_request)

        return success(options.model_dump(), "获取表单选项成功")

    except Exception as e:
        return bad_request(f"获取表单选项失败: {str(e)}")


@router.get("/", summary="分页查询检查记录")
async def get_inspection_records_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: Session = Depends(get_db),
):
    """分页查询检查记录列表"""
    try:
        service = get_inspection_records_service(session)
        page_params = PageParams(page=page, size=size)

        # 过滤条件
        filters = {}
        items, total = service.get_list(page_params, filters)

        # 响应格式
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

        return success(response_data, "查询检查记录列表成功")

    except Exception as e:
        return bad_request(f"查询检查记录列表失败: {str(e)}")


@router.post("/damage-reference", summary="获取病害参考信息")
async def get_damage_reference_info(
    request: DamageReferenceRequest,
    session: Session = Depends(get_db),
):
    """根据病害类型获取参考信息"""
    try:
        service = get_inspection_records_service(session)
        result = service.get_damage_reference_info(request)

        return success(result.model_dump(), "获取病害参考信息成功")

    except Exception as e:
        return bad_request(f"获取病害参考信息失败: {str(e)}")


@router.delete("/", summary="批量删除检查记录")
async def delete_all_inspection_records(session: Session = Depends(get_db)):
    """批量软删除所有检查记录"""
    try:
        service = get_inspection_records_service(session)
        deleted_count = service.delete_all()

        return success(
            {"deleted_count": deleted_count}, f"成功删除 {deleted_count} 条检查记录"
        )

    except Exception as e:
        return bad_request(f"批量删除检查记录失败: {str(e)}")


@router.get("/{record_id}", summary="获取检查记录详情")
async def get_inspection_record(
    record_id: int,
    session: Session = Depends(get_db),
):
    """根据ID获取检查记录详情"""
    try:
        service = get_inspection_records_service(session)
        result = service.get_record_with_details(record_id)

        return success(result.model_dump(), "获取检查记录详情成功")

    except NotFoundException as e:
        return bad_request(str(e))
    except Exception as e:
        return bad_request(f"获取检查记录详情失败: {str(e)}")


@router.put("/{record_id}", summary="更新检查记录")
async def update_inspection_record(
    record_id: int,
    update_data: InspectionRecordsUpdate,
    session: Session = Depends(get_db),
):
    """更新检查记录"""
    try:
        service = get_inspection_records_service(session)
        result = service.update(record_id, update_data)

        return success(result.model_dump(), "更新检查记录成功")

    except (NotFoundException, ValidationException) as e:
        return bad_request(str(e))
    except Exception as e:
        return bad_request(f"更新检查记录失败: {str(e)}")


@router.delete("/{record_id}", summary="删除检查记录")
async def delete_inspection_record(record_id: int, session: Session = Depends(get_db)):
    """删除检查记录"""
    try:
        service = get_inspection_records_service(session)
        success_flag = service.delete(record_id, cascade=False)

        if not success_flag:
            raise NotFoundException(
                resource="InspectionRecords", identifier=str(record_id)
            )

        return success(None, "删除检查记录成功")

    except NotFoundException as e:
        return bad_request(str(e))
    except Exception as e:
        return bad_request(f"删除检查记录失败: {str(e)}")
