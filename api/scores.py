from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Optional

from config.database import get_db
from services.scores import get_scores_service
from services.base_crud import PageParams
from schemas.scores import (
    ScoreListRequest,
    WeightAllocationRequest,
    WeightAllocationResponse,
    WeightAllocationSaveRequest,
)
from utils.responses import success, bad_request
from exceptions import NotFoundException

router = APIRouter(prefix="/scores", tags=["评分管理"])


@router.get("/list-weight", summary="查询权重分配列表")
async def get_scores_list(
    # page: int = Query(1, ge=1, description="页码"),
    # size: int = Query(20, ge=1, le=100, description="每页数量"),
    bridge_instance_name: str = Query(..., description="桥梁实例名称"),
    bridge_type_id: int = Query(..., description="桥梁类型ID"),
    assessment_unit_instance_name: Optional[str] = Query(
        None, description="评定单元实例名称"
    ),
    # assessment_unit_id: Optional[str] = Query(None, description="评定单元ID"),
    session: Session = Depends(get_db),
):
    """
    查询权重分配列表
    """
    service = get_scores_service(session)

    request = ScoreListRequest(
        bridge_instance_name=bridge_instance_name,
        assessment_unit_instance_name=assessment_unit_instance_name,
        # assessment_unit_id=assessment_unit_id,
        bridge_type_id=bridge_type_id,
    )

    # page_params = PageParams(page=page, size=size)

    items, total = service.get_score_list(request)

    response_data = {
        "items": items,
        "total": total,
        # "page": page,
        # "size": size,
    }

    return success(response_data, "查询权重分配列表成功")


@router.get("/cascade-options", summary="获取权重分配分页查询级联下拉选项")
async def get_scores_cascade_options(
    bridge_instance_name: Optional[str] = Query(None, description="桥梁实例名称"),
    assessment_unit_instance_name: Optional[str] = Query(
        None, description="评定单元实例名称"
    ),
    session: Session = Depends(get_db),
):
    """获取权重分配分页查询的级联下拉选项"""
    service = get_scores_service(session)

    options = service.get_cascade_options(
        bridge_instance_name=bridge_instance_name,
        assessment_unit_instance_name=assessment_unit_instance_name,
    )

    return success(options, "获取级联下拉选项成功")


@router.post("/weight-allocation", summary="权重分配计算")
async def calculate_weight_allocation(
    request: WeightAllocationRequest,
    session: Session = Depends(get_db),
):
    """
    权重分配计算
    """
    service = get_scores_service(session)

    items, total = service.calculate_weight_allocation(request)

    response_data = {
        "calculation_mode": request.calculation_mode,
        "items": items,
        "total": total,
    }

    return success(response_data, "权重分配计算成功")


@router.post("/weight-allocation/save", summary="保存权重分配数据")
async def save_weight_allocation(
    request: WeightAllocationSaveRequest,
    session: Session = Depends(get_db),
):
    """
    保存权重分配数据
    """
    service = get_scores_service(session)

    success_result = service.save_weight_allocation(request)

    return success(None, "权重分配数据保存成功")


@router.get("", summary="查询评分列表")
async def get_scores_table_data(
    bridge_instance_name: str = Query(..., description="桥梁实例名称"),
    bridge_type_id: int = Query(..., description="桥梁类型ID"),
    assessment_unit_instance_name: Optional[str] = Query(
        None, description="评定单元实例名称"
    ),
    session: Session = Depends(get_db),
):
    """
    查询评分列表数据
    """
    service = get_scores_service(session)

    request = ScoreListRequest(
        bridge_instance_name=bridge_instance_name,
        assessment_unit_instance_name=assessment_unit_instance_name,
        bridge_type_id=bridge_type_id,
    )

    table_data = service.get_score_table_data(request)

    return success(table_data, "查询评分表格数据成功")


@router.post("/calculate-score", summary="计算评分")
async def calculate_score(
    user_id: Optional[int] = Query(None, description="用户ID"),
    bridge_instance_name: str = Query(..., description="桥梁实例名称"),
    bridge_type_id: int = Query(..., description="桥梁类型ID"),
    assessment_unit_instance_name: Optional[str] = Query(
        None, description="评定单元实例名称"
    ),
    session: Session = Depends(get_db),
):
    """
    计算评分
    """
    service = get_scores_service(session)

    request = ScoreListRequest(
        bridge_instance_name=bridge_instance_name,
        assessment_unit_instance_name=assessment_unit_instance_name,
        bridge_type_id=bridge_type_id,
        user_id=user_id,
    )

    result = service.calculate_score(request)

    return success(result, "评分计算成功")
