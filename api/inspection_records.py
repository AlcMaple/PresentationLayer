from fastapi import APIRouter, Depends, Query, Form, File, UploadFile
from sqlmodel import Session
from typing import Optional
from io import BytesIO
from fastapi.responses import StreamingResponse

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


@router.post("", summary="创建检查记录")
async def create_inspection_record(
    # 表单数据
    user_id: Optional[int] = Form(None, description="用户ID"),
    bridge_instance_name: str = Form(..., description="桥梁类别实例名称"),
    bridge_type_id: int = Form(..., description="桥梁类型ID"),
    part_id: int = Form(..., description="部位ID"),
    component_type_id: int = Form(..., description="部件类型ID"),
    component_form_id: int = Form(..., description="构件形式ID"),
    damage_type_code: str = Form(..., description="病害类型编码"),
    scale_code: str = Form(..., description="标度编码"),
    assessment_unit_instance_name: str = Form(None, description="评定单元实例名称"),
    structure_id: int = Form(..., description="结构类型ID"),
    damage_location: Optional[str] = Form(None, description="病害位置"),
    damage_description: Optional[str] = Form(None, description="病害程度"),
    component_name: Optional[str] = Form(None, description="构件名称"),
    # 文件上传
    image: UploadFile = File(default=None, description="病害图片"),
    session: Session = Depends(get_db),
):
    """创建新的检查记录"""
    service = get_inspection_records_service(session)
    # 表单数据
    form_data = InspectionRecordsCreate(
        user_id=user_id,
        bridge_instance_name=bridge_instance_name,
        assessment_unit_instance_name=assessment_unit_instance_name,
        bridge_type_id=bridge_type_id,
        part_id=part_id,
        structure_id=structure_id,
        component_type_id=component_type_id,
        component_form_id=component_form_id,
        damage_type_code=damage_type_code,
        scale_code=scale_code,
        damage_location=damage_location,
        damage_description=damage_description,
        component_name=component_name,
    )

    result = await service.create(form_data, image)
    return success(result.model_dump(), "创建检查记录成功")


@router.get("/form-options", summary="根据路径获取表单选项")
async def get_form_options_by_path(
    path_request: PathValidationRequest = Depends(),
    session: Session = Depends(get_db),
):
    """获取病害类型和对应的标度选项"""
    service = get_inspection_records_service(session)
    options = service.get_form_options_by_path(path_request)

    return success(options.model_dump(), "获取表单选项成功")


@router.get("", summary="分页查询检查记录")
async def get_inspection_records_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID，用于过滤指定用户的记录"),
    # 路径过滤条件
    part_id: Optional[int] = Query(None, description="部位ID"),
    structure_id: Optional[int] = Query(None, description="结构类型ID"),
    component_type_id: Optional[int] = Query(None, description="部件类型ID"),
    component_form_id: Optional[int] = Query(None, description="构件形式ID"),
    session: Session = Depends(get_db),
):
    """分页查询检查记录列表"""
    try:
        service = get_inspection_records_service(session)
        page_params = PageParams(page=page, size=size)

        # 过滤条件
        filters = {}

        # 用户ID过滤（没有表示返回所有的记录）
        if user_id is not None:
            filters["user_id"] = user_id

        # 路径过滤条件
        if part_id is not None:
            filters["part_id"] = part_id
        if structure_id is not None:
            filters["structure_id"] = structure_id
        if component_type_id is not None:
            filters["component_type_id"] = component_type_id
        if component_form_id is not None:
            filters["component_form_id"] = component_form_id

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


@router.get("/damage-reference", summary="获取病害参考信息")
async def get_damage_reference_info(
    request: DamageReferenceRequest = Depends(),
    session: Session = Depends(get_db),
):
    """根据病害类型获取参考信息"""
    service = get_inspection_records_service(session)
    result = service.get_damage_reference_info(request)

    return success(result.model_dump(), "获取病害参考信息成功")


@router.delete("", summary="按路径批量删除检查记录")
async def delete_inspection_records_by_path(
    path_request: PathValidationRequest, session: Session = Depends(get_db)
):
    """批量软删除检查记录"""
    service = get_inspection_records_service(session)

    # 过滤条件
    filters = {
        "bridge_instance_name": path_request.bridge_instance_name,
        "bridge_type_id": path_request.bridge_type_id,
        "part_id": path_request.part_id,
        "component_type_id": path_request.component_type_id,
        "component_form_id": path_request.component_form_id,
    }

    # 添加用户ID过滤条件，防止删除其他用户的数据
    if path_request.user_id is not None:
        filters["user_id"] = path_request.user_id
    else:
        # user_id为空代表管理员创建的记录
        filters["user_id"] = None

    if path_request.assessment_unit_instance_name is not None:
        filters["assessment_unit_instance_name"] = (
            path_request.assessment_unit_instance_name
        )

    if path_request.structure_id is not None:
        filters["structure_id"] = path_request.structure_id

    # 批量删除
    deleted_count = service.delete_all(filters)

    return success(
        {"deleted_count": deleted_count},
        f"成功删除 {deleted_count} 条检查记录",
    )


@router.get("/export", summary="导出检查记录为Excel")
async def export_inspection_records(
    session: Session = Depends(get_db), data: PathValidationRequest = Depends()
):
    service = get_inspection_records_service(session)
    excel_bytes = service.export_template(data)
    buffer = BytesIO(excel_bytes)

    # 文件名
    filename = "inspection_records_template.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import", summary="导入检查记录 Excel")
async def import_inspection_records_excel(
    user_id: Optional[int] = Form(None, description="用户ID"),
    bridge_instance_name: str = Form(..., description="桥梁类别实例名称"),
    bridge_type_id: int = Form(..., description="桥梁类型ID"),
    part_id: int = Form(..., description="部位ID"),
    component_type_id: int = Form(..., description="部件类型ID"),
    component_form_id: int = Form(..., description="构件形式ID"),
    assessment_unit_instance_name: str = Form(None, description="评定单元实例名称"),
    structure_id: int = Form(..., description="结构类型ID"),
    file: UploadFile = File(..., description="检查记录 Excel 文件"),
    session: Session = Depends(get_db),
):
    """
    导入检查记录 Excel
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        return bad_request("文件类型错误，请上传Excel文件(.xlsx或.xls格式)")

    # 读取 Excel 文件内容
    file_content = await file.read()

    # 表单数据
    form_data = PathValidationRequest(
        user_id=user_id,
        bridge_instance_name=bridge_instance_name,
        assessment_unit_instance_name=assessment_unit_instance_name,
        bridge_type_id=bridge_type_id,
        part_id=part_id,
        structure_id=structure_id,
        component_type_id=component_type_id,
        component_form_id=component_form_id,
    )

    service = get_inspection_records_service(session)
    import_result = await service.import_from_excel(
        file_content, form_data, file.filename
    )
    return success(import_result, "导入检查记录成功")


@router.get("/filter-options", summary="获取分页查询过滤选项")
async def get_inspection_records_filter_options(
    session: Session = Depends(get_db),
):
    """获取检查记录分页查询的过滤选项"""
    service = get_inspection_records_service(session)
    options = service.get_filter_options()

    return success(options, "获取过滤选项成功")


@router.get("/{record_id}", summary="获取检查记录详情")
async def get_inspection_record(
    record_id: int,
    session: Session = Depends(get_db),
):
    """根据ID获取检查记录详情"""
    service = get_inspection_records_service(session)
    result = service.get_record_with_details(record_id)

    return success(result.model_dump(), "获取检查记录详情成功")


@router.put("/{record_id}", summary="更新检查记录")
async def update_inspection_record(
    record_id: int,
    # 表单数据
    damage_type_code: str = Form(None, description="病害类型编码"),
    scale_code: str = Form(None, description="标度编码"),
    damage_location: str = Form(None, description="病害位置"),
    damage_description: str = Form(None, description="病害程度"),
    component_name: str = Form(None, description="构件名称"),
    # 文件上传
    image: UploadFile = File(default=None, description="病害图片"),
    session: Session = Depends(get_db),
):
    """更新检查记录"""
    service = get_inspection_records_service(session)
    update_data = InspectionRecordsUpdate(
        damage_type_code=damage_type_code,
        scale_code=scale_code,
        damage_location=damage_location,
        damage_description=damage_description,
        component_name=component_name,
    )
    result = await service.update(record_id, update_data, image)

    return success(result.model_dump(), "更新检查记录成功")


@router.delete("/{record_id}", summary="删除检查记录")
async def delete_inspection_record(record_id: int, session: Session = Depends(get_db)):
    """删除检查记录"""
    service = get_inspection_records_service(session)
    success_flag = service.delete(record_id, cascade=False)

    if not success_flag:
        raise NotFoundException(resource="InspectionRecords", identifier=str(record_id))

    return success(None, "删除检查记录成功")
