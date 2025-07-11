from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, and_, func
from typing import Optional, List
from sqlalchemy import desc, asc
from datetime import datetime

from config.database import get_db
from services.base_crud import BaseCRUDService, PageParams
from models import BridgeScales
from models.enums import ScalesType
from api.schemas.bridge_scales import (
    BridgeScalesCreate,
    BridgeScalesUpdate,
    BridgeScalesResponse,
)
from utils.responses import success
from exceptions import NotFoundException, DuplicateException
from services.code_generator import get_code_generator

router = APIRouter(prefix="/bridge_scales", tags=["标度管理"])


@router.get("/", summary="分页查询标度列表")
async def get_bridge_scales_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="标度名称模糊查询"),
    scale_type: Optional[ScalesType] = Query(
        ScalesType.NUMERIC,
        description="标度类型筛选（NUMERIC(数值)/PERCENTAGE(百分比)/RANGE(范围)/TEXT(文本)）",
    ),
    scale_value: Optional[int] = Query(None, description="标度值"),
    min_value: Optional[int] = Query(None, description="范围最小值"),
    max_value: Optional[int] = Query(None, description="范围最大值"),
    unit: Optional[str] = Query(None, description="单位"),
    display_text: Optional[str] = Query(None, description="显示文本模糊查询"),
    session: Session = Depends(get_db),
):
    """分页查询标度列表"""

    # 查询条件
    statement = select(BridgeScales)
    count_statement = select(func.count(BridgeScales.id))

    # 筛选条件
    conditions = [BridgeScales.is_active == True]

    if name:
        conditions.append(BridgeScales.name.like(f"%{name}%"))
    if scale_type:
        conditions.append(BridgeScales.scale_type == scale_type)
    if scale_value is not None:
        conditions.append(BridgeScales.scale_value == scale_value)
    if min_value is not None:
        conditions.append(BridgeScales.min_value == min_value)
    if max_value is not None:
        conditions.append(BridgeScales.max_value == max_value)
    if unit:
        conditions.append(BridgeScales.unit == unit)
    if display_text:
        conditions.append(BridgeScales.display_text.like(f"%{display_text}%"))

    if conditions:
        statement = statement.where(and_(*conditions))
        count_statement = count_statement.where(and_(*conditions))

    # 排序和分页
    statement = statement.order_by(
        asc(BridgeScales.scale_value), asc(BridgeScales.sort_order)
    )
    offset = (page - 1) * size
    statement = statement.offset(offset).limit(size)

    # 查询
    items = session.exec(statement).all()
    total = session.exec(count_statement).first() or 0

    list_items = [
        BridgeScalesResponse.model_validate(item).model_dump() for item in items
    ]
    response_item = {
        "items": list_items,
        "total": total,
        "page": page,
        "size": size,
    }
    return success(response_item, "查询成功")


@router.post("/", summary="创建标度")
async def create_bridge_scales(
    scale_data: BridgeScalesCreate, session: Session = Depends(get_db)
):
    """创建标度"""
    try:
        obj_data = scale_data.model_dump(exclude_unset=True)

        # 处理编码
        code_generator = get_code_generator(session)
        code_value = obj_data.get("code")
        if not code_value or not code_value.strip():
            obj_data["code"] = code_generator.generate_code("bridge_scales")
        else:
            # 检查编码
            existing_code = session.exec(
                select(BridgeScales).where(
                    and_(
                        BridgeScales.code == code_value.strip(),
                        BridgeScales.is_active == True,
                    )
                )
            ).first()
            if existing_code:
                raise DuplicateException(
                    resource="BridgeScales", field="code", value=code_value.strip()
                )
            obj_data["code"] = code_value.strip()

        # 根据标度类型处理字段
        scale_type = obj_data.get("scale_type")

        if scale_type == ScalesType.NUMERIC:
            # 数值类型
            obj_data["min_value"] = None
            obj_data["max_value"] = None
            obj_data["unit"] = None
            obj_data["display_text"] = None

            # 检查标度值是否已存在
            if obj_data.get("scale_value") is not None:
                existing = session.exec(
                    select(BridgeScales).where(
                        and_(
                            BridgeScales.scale_value == obj_data["scale_value"],
                            BridgeScales.is_active == True,
                        )
                    )
                ).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales",
                        field="标度值",
                        value=str(obj_data["scale_value"]),
                    )

        elif scale_type in [ScalesType.RANGE, ScalesType.PERCENTAGE]:
            # 范围类型或百分比类型
            obj_data["scale_value"] = None
            obj_data["display_text"] = None

            # 检查范围是否已存在
            min_value = obj_data.get("min_value")
            max_value = obj_data.get("max_value")
            unit = obj_data.get("unit")

            if min_value is not None and max_value is not None and unit:
                existing = session.exec(
                    select(BridgeScales).where(
                        and_(
                            BridgeScales.min_value == min_value,
                            BridgeScales.max_value == max_value,
                            BridgeScales.unit == unit,
                            BridgeScales.is_active == True,
                        )
                    )
                ).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales",
                        field="范围配置",
                        value=f"最小值{min_value}-最大值{max_value}-单位{unit}",
                    )

        elif scale_type == ScalesType.TEXT:
            # 文本类型
            obj_data["scale_value"] = None
            obj_data["min_value"] = None
            obj_data["max_value"] = None
            obj_data["unit"] = None

            # 检查显示文本是否已存在
            display_text = obj_data.get("display_text")
            if display_text:
                existing = session.exec(
                    select(BridgeScales).where(
                        and_(
                            BridgeScales.display_text == display_text,
                            BridgeScales.is_active == True,
                        )
                    )
                ).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales", field="显示文本", value=display_text
                    )

        # 创建对象
        db_obj = BridgeScales(**obj_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)

        response_item = BridgeScalesResponse.model_validate(db_obj)
        return success(response_item.model_dump(), "创建成功")

    except DuplicateException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise Exception(f"创建失败: {str(e)}")


@router.delete("/{id}", summary="删除标度")
async def delete_bridge_scales(id: int, session: Session = Depends(get_db)):
    """删除标度"""
    try:
        db_obj = session.exec(
            select(BridgeScales).where(
                and_(BridgeScales.id == id, BridgeScales.is_active == True)
            )
        ).first()
        if not db_obj:
            raise NotFoundException(resource="BridgeScales", identifier=str(id))

        db_obj.is_active = False
        db_obj.updated_at = datetime.utcnow()
        session.commit()

        return success(None, "删除成功")

    except NotFoundException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise Exception(f"删除失败: {str(e)}")


@router.put("/{id}", summary="更新标度")
async def update_bridge_scales(
    id: int, scale_data: BridgeScalesUpdate, session: Session = Depends(get_db)
):
    """更新标度"""
    try:
        # 查询现有记录
        db_obj = session.exec(
            select(BridgeScales).where(
                and_(BridgeScales.id == id, BridgeScales.is_active == True)
            )
        ).first()
        if not db_obj:
            raise NotFoundException(resource="BridgeScales", identifier=str(id))

        obj_data = scale_data.model_dump(exclude_unset=True)

        # 处理编码
        if "code" in obj_data:
            code_value = obj_data["code"]
            if code_value and code_value.strip():
                # 检查编码
                existing_code = session.exec(
                    select(BridgeScales).where(
                        and_(
                            BridgeScales.code == code_value.strip(),
                            BridgeScales.id != id,
                            BridgeScales.is_active == True,
                        )
                    )
                ).first()
                if existing_code:
                    raise DuplicateException(
                        resource="BridgeScales", field="code", value=code_value.strip()
                    )
                obj_data["code"] = code_value.strip()
            else:
                obj_data.pop("code")  # 不更新编码

        # 获取标度类型
        new_scale_type = obj_data.get("scale_type", db_obj.scale_type)

        # 根据标度类型处理字段
        if new_scale_type == ScalesType.NUMERIC:
            # 数值类型
            obj_data["min_value"] = None
            obj_data["max_value"] = None
            obj_data["unit"] = None
            obj_data["display_text"] = None

            # 检查标度值是否与其他记录重复
            scale_value = obj_data.get("scale_value", db_obj.scale_value)
            if scale_value is not None:
                existing = session.exec(
                    select(BridgeScales).where(
                        and_(
                            BridgeScales.scale_value == scale_value,
                            BridgeScales.id != id,
                            BridgeScales.is_active == True,
                        )
                    )
                ).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales", field="标度值", value=str(scale_value)
                    )

        elif new_scale_type in [ScalesType.RANGE, ScalesType.PERCENTAGE]:
            # 范围类型或百分比类型
            obj_data["scale_value"] = None
            obj_data["display_text"] = None

            # 检查范围配置是否与其他记录重复
            min_value = obj_data.get("min_value", db_obj.min_value)
            max_value = obj_data.get("max_value", db_obj.max_value)
            unit = obj_data.get("unit", db_obj.unit)

            if min_value is not None and max_value is not None and unit:
                existing = session.exec(
                    select(BridgeScales).where(
                        and_(
                            BridgeScales.min_value == min_value,
                            BridgeScales.max_value == max_value,
                            BridgeScales.unit == unit,
                            BridgeScales.id != id,
                            BridgeScales.is_active == True,
                        )
                    )
                ).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales",
                        field="范围配置",
                        value=f"最小值{min_value}-最大值{max_value}-单位{unit}",
                    )

        elif new_scale_type == ScalesType.TEXT:
            # 文本类型
            obj_data["scale_value"] = None
            obj_data["min_value"] = None
            obj_data["max_value"] = None
            obj_data["unit"] = None

            # 检查显示文本是否与其他记录重复
            display_text = obj_data.get("display_text", db_obj.display_text)
            if display_text:
                existing = session.exec(
                    select(BridgeScales).where(
                        and_(
                            BridgeScales.display_text == display_text,
                            BridgeScales.id != id,
                            BridgeScales.is_active == True,
                        )
                    )
                ).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales", field="显示文本", value=display_text
                    )

        # 更新对象
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(db_obj)

        response_item = BridgeScalesResponse.model_validate(db_obj)
        return success(response_item.model_dump(), "更新成功")

    except (NotFoundException, DuplicateException):
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise Exception(f"更新失败: {str(e)}")
