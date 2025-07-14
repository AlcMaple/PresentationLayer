from typing import Optional, Dict, Any, List, Tuple
from sqlmodel import Session, select, and_, func
from sqlalchemy import asc

from models import BridgeScales
from models.enums import ScalesType
from schemas.bridge_scales import BridgeScalesCreate, BridgeScalesUpdate
from services.base_crud import BaseCRUDService, PageParams
from exceptions import NotFoundException, DuplicateException


class BridgeScalesService(
    BaseCRUDService[BridgeScales, BridgeScalesCreate, BridgeScalesUpdate]
):
    """桥梁标度服务类"""

    def __init__(self, session: Session):
        super().__init__(BridgeScales, session)

    def get_list_with_filters(
        self,
        page_params: PageParams,
        name: Optional[str] = None,
        scale_type: Optional[ScalesType] = None,
        scale_value: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        unit: Optional[str] = None,
        display_text: Optional[str] = None,
    ) -> Tuple[List[BridgeScales], int]:
        """
        分页查询标度列表
        """
        statement = select(BridgeScales)
        count_statement = select(func.count(BridgeScales.id))

        # 只查询激活的记录
        conditions = [BridgeScales.is_active == True]

        # 添加过滤条件
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

        # 应用条件
        if conditions:
            statement = statement.where(and_(*conditions))
            count_statement = count_statement.where(and_(*conditions))

        # 按标度值和排序字段排序
        statement = statement.order_by(
            asc(BridgeScales.scale_value), asc(BridgeScales.sort_order)
        )

        # 分页
        statement = statement.offset(page_params.offset).limit(page_params.size)

        # 执行查询
        items = self.session.exec(statement).all()
        total = self.session.exec(count_statement).first() or 0

        return items, total

    def create(self, obj_in: BridgeScalesCreate) -> BridgeScales:
        """
        创建标度
        """
        try:
            obj_data = obj_in.model_dump(exclude_unset=True)

            # 处理编码
            code_value = obj_data.get("code")
            if not code_value or not code_value.strip():
                obj_data["code"] = self.code_generator.generate_code("bridge_scales")
            else:
                # 检查编码重复
                existing_code = self._check_code_duplicate(code_value.strip())
                if existing_code:
                    raise DuplicateException(
                        resource="BridgeScales", field="code", value=code_value.strip()
                    )
                obj_data["code"] = code_value.strip()

            # 根据标度类型处理字段
            self._process_scale_type_fields(obj_data)

            # 检查业务规则重复
            self._check_business_duplicate(obj_data)

            # 创建对象
            db_obj = BridgeScales(**obj_data)
            self.session.add(db_obj)
            self.session.commit()
            self.session.refresh(db_obj)

            return db_obj

        except DuplicateException:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"创建失败: {str(e)}")

    def update(self, id: int, obj_in: BridgeScalesUpdate) -> Optional[BridgeScales]:
        """
        更新标度
        """
        try:
            # 查询现有记录
            db_obj = self.get_by_id(id)
            if not db_obj:
                raise NotFoundException(resource="BridgeScales", identifier=str(id))

            obj_data = obj_in.model_dump(exclude_unset=True)

            # 处理编码
            if "code" in obj_data:
                code_value = obj_data["code"]
                if code_value and code_value.strip():
                    # 检查编码重复（排除当前记录）
                    existing_code = self._check_code_duplicate(
                        code_value.strip(), exclude_id=id
                    )
                    if existing_code:
                        raise DuplicateException(
                            resource="BridgeScales",
                            field="code",
                            value=code_value.strip(),
                        )
                    obj_data["code"] = code_value.strip()
                else:
                    obj_data.pop("code")  # 不更新编码

            # 获取标度类型（新的或现有的）
            new_scale_type = obj_data.get("scale_type", db_obj.scale_type)
            obj_data["scale_type"] = new_scale_type

            # 根据标度类型处理字段
            self._process_scale_type_fields(obj_data)

            # 检查业务规则重复（排除当前记录）
            self._check_business_duplicate(obj_data, exclude_id=id, current_obj=db_obj)

            # 更新对象
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            from datetime import datetime, timezone

            db_obj.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            self.session.refresh(db_obj)

            return db_obj

        except (NotFoundException, DuplicateException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"更新失败: {str(e)}")

    def _process_scale_type_fields(self, obj_data: Dict[str, Any]) -> None:
        """
        根据标度类型处理字段
        """
        scale_type = obj_data.get("scale_type")

        if scale_type == ScalesType.NUMERIC:
            # 数值类型
            obj_data["min_value"] = None
            obj_data["max_value"] = None
            obj_data["unit"] = None
            obj_data["display_text"] = None

        elif scale_type in [ScalesType.RANGE, ScalesType.PERCENTAGE]:
            # 范围类型或百分比类型
            obj_data["scale_value"] = None
            obj_data["display_text"] = None

        elif scale_type == ScalesType.TEXT:
            # 文本类型
            obj_data["scale_value"] = None
            obj_data["min_value"] = None
            obj_data["max_value"] = None
            obj_data["unit"] = None

    def _check_code_duplicate(
        self, code: str, exclude_id: Optional[int] = None
    ) -> Optional[BridgeScales]:
        """
        检查编码重复
        """
        statement = select(BridgeScales).where(
            and_(
                BridgeScales.code == code,
                BridgeScales.is_active == True,
            )
        )

        if exclude_id:
            statement = statement.where(BridgeScales.id != exclude_id)

        return self.session.exec(statement).first()

    def _check_business_duplicate(
        self,
        obj_data: Dict[str, Any],
        exclude_id: Optional[int] = None,
        current_obj: Optional[BridgeScales] = None,
    ) -> None:
        """
        检查业务规则重复
        """
        scale_type = obj_data.get("scale_type")

        if scale_type == ScalesType.NUMERIC:
            # 检查标度值是否重复
            scale_value = obj_data.get("scale_value")
            if scale_value is not None:
                statement = select(BridgeScales).where(
                    and_(
                        BridgeScales.scale_value == scale_value,
                        BridgeScales.is_active == True,
                    )
                )
                if exclude_id:
                    statement = statement.where(BridgeScales.id != exclude_id)

                existing = self.session.exec(statement).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales",
                        field="标度值",
                        value=str(scale_value),
                    )

        elif scale_type in [ScalesType.RANGE, ScalesType.PERCENTAGE]:
            # 检查范围和百分比是否重复
            min_value = obj_data.get("min_value")
            max_value = obj_data.get("max_value")
            unit = obj_data.get("unit")

            # 更新操作，获取当前值
            if current_obj:
                min_value = (
                    min_value if min_value is not None else current_obj.min_value
                )
                max_value = (
                    max_value if max_value is not None else current_obj.max_value
                )
                unit = unit if unit is not None else current_obj.unit

            if min_value is not None and max_value is not None and unit:
                statement = select(BridgeScales).where(
                    and_(
                        BridgeScales.min_value == min_value,
                        BridgeScales.max_value == max_value,
                        BridgeScales.unit == unit,
                        BridgeScales.is_active == True,
                    )
                )
                if exclude_id:
                    statement = statement.where(BridgeScales.id != exclude_id)

                existing = self.session.exec(statement).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales",
                        field="范围配置",
                        value=f"最小值{min_value}-最大值{max_value}-单位{unit}",
                    )

        elif scale_type == ScalesType.TEXT:
            # 检查显示文本是否重复
            display_text = obj_data.get("display_text")

            # 更新操作，获取当前值
            if current_obj:
                display_text = (
                    display_text
                    if display_text is not None
                    else current_obj.display_text
                )

            if display_text:
                statement = select(BridgeScales).where(
                    and_(
                        BridgeScales.display_text == display_text,
                        BridgeScales.is_active == True,
                    )
                )
                if exclude_id:
                    statement = statement.where(BridgeScales.id != exclude_id)

                existing = self.session.exec(statement).first()
                if existing:
                    raise DuplicateException(
                        resource="BridgeScales", field="显示文本", value=display_text
                    )


def get_bridge_scales_service(session: Session) -> BridgeScalesService:
    """获取桥梁标度服务实例"""
    return BridgeScalesService(session)
