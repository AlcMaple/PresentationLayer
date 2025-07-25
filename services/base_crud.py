from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlmodel import SQLModel, Session, select, and_
from sqlalchemy import func, desc, asc, update
from abc import ABC
from datetime import datetime
from pydantic import BaseModel, Field

from exceptions import NotFoundException, DuplicateException
from services.code_generator import get_code_generator
from services.path_cascade import get_path_cascade_service

# 泛型变量定义
ModelType = TypeVar("ModelType", bound=SQLModel)  # 数据模型类型
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)  # 创建模型类型
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)  # 更新模型类型


class PageParams(BaseModel):
    """分页参数"""

    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        """偏移量"""
        return (self.page - 1) * self.size


class BaseCRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    通用CRUD服务基类
    """

    def __init__(self, model: Type[ModelType], session: Session):
        """
        初始化CRUD服务
        Args:
            model: 数据模型类
            session: 数据库会话
        """
        self.model = model
        self.session = session
        self.code_generator = get_code_generator(session)

    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[ModelType]:
        """
        根据ID查询单条记录
        Args:
            id: 记录ID
            include_deleted: 是否包含已删除记录
        Returns:
            模型实例或None
        """
        try:
            statement = select(self.model).where(self.model.id == id)
            if hasattr(self.model, "is_active") and not include_deleted:
                statement = statement.where(self.model.is_active == True)

            result = self.session.exec(statement).first()
            return result
        except Exception as e:
            print(f"查询ID为{id}的记录时出错: {e}")
            return None

    def get_by_code(
        self, code: str, include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        根据编码查询单条记录
        Args:
            code: 记录编码
            include_deleted: 是否包含已删除记录
        Returns:
            模型实例或None
        """
        try:
            statement = select(self.model).where(self.model.code == code)
            if hasattr(self.model, "is_active") and not include_deleted:
                statement = statement.where(self.model.is_active == True)

            result = self.session.exec(statement).first()
            return result
        except Exception as e:
            print(f"查询编码为{code}的记录时出错: {e}")
            return None

    def get_list(
        self,
        page_params: PageParams,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False,
    ) -> tuple[List[ModelType], int]:
        """
        分页查询列表
        Args:
            page_params: 分页参数
            filters: 查询过滤条件字典
        Returns:
            (记录列表, 总数)
        """
        try:
            statement = select(self.model)
            count_statement = select(func.count(self.model.id))

            conditions = []
            if hasattr(self.model, "is_active") and not include_deleted:
                conditions.append(self.model.is_active == True)

            # 过滤
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
                conditions.extend(filter_conditions)

            if conditions:
                statement = statement.where(and_(*conditions))
                count_statement = count_statement.where(and_(*conditions))

            # 默认按创建时间倒序排列
            if hasattr(self.model, "created_at"):
                statement = statement.order_by(desc(self.model.created_at))
            elif hasattr(self.model, "sort_order"):
                statement = statement.order_by(asc(self.model.sort_order))

            # 分页
            statement = statement.offset(page_params.offset).limit(page_params.size)

            items = self.session.exec(statement).all()
            total = self.session.exec(count_statement).first() or 0

            return items, total

        except Exception as e:
            print(f"查询列表时出错: {e}")
            return [], 0

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        创建新记录
        Args:
            obj_in: 创建数据模型
        Returns:
            创建的模型实例
        Raises:
            DuplicateException: 重复创建
        """
        try:
            # 转换为数据库模型
            obj_data = obj_in.model_dump(exclude_unset=True)

            # 编码
            if hasattr(self.model, "code"):
                code_value = obj_data.get("code")
                obj_data["code"] = self.code_generator.assign_or_generate_code(
                    self.model.__tablename__, code_value
                )

            # 检查名称
            if hasattr(self.model, "name") and "name" in obj_data:
                statement = select(self.model).where(
                    self.model.name == obj_data["name"]
                )
                # 排除已删除的记录
                if hasattr(self.model, "is_active"):
                    statement = statement.where(self.model.is_active == True)
                existing = self.session.exec(statement).first()
                if existing:
                    raise DuplicateException(
                        resource=self.model.__name__,
                        field="name",
                        value=obj_data["name"],
                    )

            # 创建对象
            db_obj = self.model(**obj_data)
            self.session.add(db_obj)
            self.session.commit()
            self.session.refresh(db_obj)

            return db_obj

        except DuplicateException:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            print(f"创建记录时出错: {e}")
            raise Exception(f"创建失败: {str(e)}")

    def update(self, id: int, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """
        更新记录
        Args:
            id: 记录ID
            obj_in: 更新数据模型
        Returns:
            更新后的模型实例
        Raises:
            NotFoundException: 记录不存在
        """
        try:
            # 查询
            db_obj = self.get_by_id(id)
            if not db_obj:
                raise NotFoundException(
                    resource=self.model.__name__, identifier=str(id)
                )
            obj_data = obj_in.model_dump(exclude_unset=True)

            # 编码
            if hasattr(self.model, "code") and "code" in obj_data:
                code_value = obj_data["code"]
                # 如果编码为空，移除该字段，保持原编码不变
                if not code_value or not code_value.strip():
                    obj_data.pop("code")
                else:
                    # 检查编码重复（排除当前记录）
                    code_value = code_value.strip()
                    statement = select(self.model).where(
                        and_(self.model.code == code_value, self.model.id != id)
                    )
                    # 排除已删除的记录
                    if hasattr(self.model, "is_active"):
                        statement = statement.where(self.model.is_active == True)
                    existing = self.session.exec(statement).first()
                    if existing:
                        raise DuplicateException(
                            resource=self.model.__name__,
                            field="code",
                            value=code_value,
                        )
                    obj_data["code"] = code_value

            # 检查名称
            if hasattr(self.model, "name") and "name" in obj_data:
                statement = select(self.model).where(
                    and_(self.model.name == obj_data["name"], self.model.id != id)
                )
                existing = self.session.exec(statement).first()
                if existing:
                    raise DuplicateException(
                        resource=self.model.__name__,
                        field="name",
                        value=obj_data["name"],
                    )

            # 更新
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = datetime.utcnow()

            self.session.commit()
            self.session.refresh(db_obj)

            return db_obj

        except (NotFoundException, DuplicateException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            print(f"更新记录时出错: {e}")
            raise Exception(f"更新失败: {str(e)}")

    def delete(self, id: int, cascade: bool = True) -> bool:
        """
        删除记录
        Args:
            id: 记录ID
        Returns:
            是否删除成功
        Raises:
            NotFoundException: 记录不存在
        """
        try:
            db_obj = self.get_by_id(id)
            if not db_obj:
                raise NotFoundException(
                    resource=self.model.__name__, identifier=str(id)
                )

            # 删除
            if hasattr(db_obj, "is_active"):
                db_obj.is_active = False
                if hasattr(db_obj, "updated_at"):
                    db_obj.updated_at = datetime.utcnow()
                self.session.commit()

                # 级联删除paths表中的相关记录
                if cascade and self._should_cascade_delete():
                    self._perform_cascade_delete(id)
            else:
                self.session.delete(db_obj)
                self.session.commit()

            return True

        except NotFoundException:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            print(f"删除记录时出错: {e}")
            raise Exception(f"删除失败: {str(e)}")

    def _build_filter_conditions(self, filters: Dict[str, Any]) -> List[Any]:
        """
        查询过滤
        Args:
            filters: 过滤条件字典
        Returns:
            条件列表
        """
        conditions = []

        for field, value in filters.items():
            if value is None:
                continue

            if not hasattr(self.model, field):
                continue

            field_attr = getattr(self.model, field)

            # 字符串模糊查询
            if isinstance(value, str) and field in ["name"]:
                conditions.append(field_attr.like(f"%{value}%"))
            # ID字段匹配
            elif isinstance(value, int) and field.endswith("_id"):
                conditions.append(field_attr == value)

        return conditions

    def _should_cascade_delete(self) -> bool:
        """
        判断是否需要级联删除
        Returns:
            是否需要级联删除
        """
        # 需要级联删除的表列表
        cascade_tables = [
            "categories",
            "assessment_units",
            "bridge_types",
            "bridge_parts",
            "bridge_structures",
            "bridge_component_types",
            "bridge_component_forms",
            "bridge_diseases",
            "bridge_scales",
            "bridge_qualities",
            "bridge_quantities",
        ]

        return (
            hasattr(self.model, "__tablename__")
            and self.model.__tablename__ in cascade_tables
        )

    def _perform_cascade_delete(self, record_id: int) -> None:
        """
        执行级联删除
        Args:
            record_id: 被删除的记录ID
        """
        try:
            cascade_service = get_path_cascade_service(self.session)
            table_name = self.model.__tablename__

            # 级联删除
            affected_rows = cascade_service.cascade_delete_by_table(
                table_name, record_id
            )

            if affected_rows > 0:
                print(
                    f"级联删除完成: 表 {table_name} ID {record_id}, 影响 {affected_rows} 条路径"
                )

        except Exception as e:
            print(f"级联删除时出错: {e}")
            pass

    def delete_all(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        批量软删除记录
        Args:
            filters: 删除条件过滤器，如果为None则删除所有记录
        Returns:
            删除的记录数量
        Raises:
            Exception: 删除失败
        """
        try:
            # 构建更新条件
            conditions = []

            # 只删除活跃记录
            if hasattr(self.model, "is_active"):
                conditions.append(self.model.is_active == True)
            else:
                raise Exception(f"模型 {self.model.__name__} 不支持软删除")

            # 添加过滤条件
            if filters:
                filter_conditions = self._build_filter_conditions(filters)
                conditions.extend(filter_conditions)

            # 更新
            update_values = {"is_active": False}
            if hasattr(self.model, "updated_at"):
                update_values["updated_at"] = datetime.utcnow()

            stmt = update(self.model).where(and_(*conditions)).values(**update_values)
            result = self.session.execute(stmt)
            affected_rows = result.rowcount

            self.session.commit()

            return affected_rows

        except Exception as e:
            self.session.rollback()
            print(f"批量删除记录时出错: {e}")
            raise Exception(f"批量删除失败: {str(e)}")


def get_base_crud_service(
    model: Type[ModelType], session: Session
) -> BaseCRUDService[ModelType, CreateSchemaType, UpdateSchemaType]:
    """
    获取通用CRUD服务
    Args:
        model: 数据模型类
        session: 数据库会话
    Returns:
        CRUD服务实例
    """
    return BaseCRUDService(model, session)
