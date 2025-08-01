from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, and_
from datetime import datetime, timezone

from models.user_paths import UserPaths
from models import (
    Categories,
    BridgeTypes,
    BridgeParts,
    BridgeStructures,
    BridgeComponentTypes,
    BridgeComponentForms,
    Paths,
    AssessmentUnit,
)
from schemas.user_paths import (
    UserPathsCreate,
    UserPathsUpdate,
    UserPathsResponse,
    CascadeOptionsRequest,
    CascadeOptionsResponse,
)
from services.base_crud import BaseCRUDService, PageParams
from exceptions import NotFoundException, ValidationException


class UserPathsService(BaseCRUDService[UserPaths, UserPathsCreate, UserPathsUpdate]):
    """用户路径服务类"""

    def __init__(self, session: Session):
        super().__init__(UserPaths, session)

    def get_cascade_options(
        self, request: CascadeOptionsRequest
    ) -> CascadeOptionsResponse:
        """
        获取级联下拉选项

        Args:
            request: 级联选项请求

        Returns:
            级联选项响应
        """
        try:
            # 获取桥梁类型选项
            bridge_type_options = self._get_bridge_type_options()

            # 获取部位选项
            part_options = self._get_part_options(request.bridge_type_id)

            # 获取结构类型选项
            structure_options = self._get_structure_options(
                request.bridge_type_id, request.part_id
            )

            # 获取部件类型选项
            component_type_options = self._get_component_type_options(
                request.bridge_type_id, request.part_id, request.structure_id
            )

            # 获取构件形式选项
            component_form_options = self._get_component_form_options(
                request.bridge_type_id,
                request.part_id,
                request.structure_id,
                request.component_type_id,
            )

            return CascadeOptionsResponse(
                bridge_type_options=bridge_type_options,
                part_options=part_options,
                structure_options=structure_options,
                component_type_options=component_type_options,
                component_form_options=component_form_options,
            )

        except Exception as e:
            print(f"获取级联选项时出错: {e}")
            raise Exception(f"获取级联选项失败: {str(e)}")

    def _get_bridge_type_options(self) -> List[Dict[str, Any]]:
        """获取桥梁类型选项"""
        try:
            # 从paths表获取存在的桥梁类型ID
            existing_bridge_type_ids_stmt = (
                select(Paths.bridge_type_id)
                .where(and_(Paths.bridge_type_id.is_not(None), Paths.is_active == True))
                .distinct()
            )
            existing_ids = self.session.exec(existing_bridge_type_ids_stmt).all()

            if not existing_ids:
                return []

            # 查询桥梁类型详细信息
            stmt = (
                select(BridgeTypes.id, BridgeTypes.name)
                .where(
                    and_(
                        BridgeTypes.id.in_(existing_ids), BridgeTypes.is_active == True
                    )
                )
                .order_by(BridgeTypes.name)
            )

            results = self.session.exec(stmt).all()
            return [{"id": r[0], "name": r[1]} for r in results]

        except Exception as e:
            print(f"获取桥梁类型选项时出错: {e}")
            return []

    def _get_part_options(self, bridge_type_id: int) -> List[Dict[str, Any]]:
        """获取部位选项"""
        try:
            existing_part_ids_stmt = (
                select(Paths.part_id)
                .where(
                    and_(
                        Paths.bridge_type_id == bridge_type_id,
                        Paths.part_id.is_not(None),
                        Paths.is_active == True,
                    )
                )
                .distinct()
            )
            existing_ids = self.session.exec(existing_part_ids_stmt).all()

            if not existing_ids:
                return []

            # 查询部位详细信息
            stmt = (
                select(BridgeParts.id, BridgeParts.name)
                .where(
                    and_(
                        BridgeParts.id.in_(existing_ids), BridgeParts.is_active == True
                    )
                )
                .order_by(BridgeParts.name)
            )

            results = self.session.exec(stmt).all()
            return [{"id": r[0], "name": r[1]} for r in results]

        except Exception as e:
            print(f"获取部位选项时出错: {e}")
            return []

    def _get_structure_options(
        self, bridge_type_id: int, part_id: int
    ) -> List[Dict[str, Any]]:
        """获取结构类型选项"""
        try:
            existing_structure_ids_stmt = (
                select(Paths.structure_id)
                .where(
                    and_(
                        Paths.bridge_type_id == bridge_type_id,
                        Paths.part_id == part_id,
                        Paths.structure_id.is_not(None),
                        Paths.is_active == True,
                    )
                )
                .distinct()
            )
            existing_ids = self.session.exec(existing_structure_ids_stmt).all()

            if not existing_ids:
                return []

            # 查询结构类型详细信息
            stmt = (
                select(BridgeStructures.id, BridgeStructures.name)
                .where(
                    and_(
                        BridgeStructures.id.in_(existing_ids),
                        BridgeStructures.is_active == True,
                    )
                )
                .order_by(BridgeStructures.name)
            )

            results = self.session.exec(stmt).all()
            return [{"id": r[0], "name": r[1]} for r in results]

        except Exception as e:
            print(f"获取结构类型选项时出错: {e}")
            return []

    def _get_component_type_options(
        self, bridge_type_id: int, part_id: int, structure_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """获取部件类型选项"""
        try:
            # 查询条件
            conditions = [
                Paths.bridge_type_id == bridge_type_id,
                Paths.part_id == part_id,
                Paths.component_type_id.is_not(None),
                Paths.is_active == True,
            ]

            # 处理结构类型条件
            if structure_id is not None:
                conditions.append(Paths.structure_id == structure_id)
            else:
                conditions.append(Paths.structure_id.is_(None))

            existing_component_type_ids_stmt = (
                select(Paths.component_type_id).where(and_(*conditions)).distinct()
            )
            existing_ids = self.session.exec(existing_component_type_ids_stmt).all()

            if not existing_ids:
                return []

            # 查询部件类型详细信息
            stmt = (
                select(BridgeComponentTypes.id, BridgeComponentTypes.name)
                .where(
                    and_(
                        BridgeComponentTypes.id.in_(existing_ids),
                        BridgeComponentTypes.is_active == True,
                    )
                )
                .order_by(BridgeComponentTypes.name)
            )

            results = self.session.exec(stmt).all()
            return [{"id": r[0], "name": r[1]} for r in results]

        except Exception as e:
            print(f"获取部件类型选项时出错: {e}")
            return []

    def _get_component_form_options(
        self,
        bridge_type_id: int,
        part_id: int,
        structure_id: Optional[int],
        component_type_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        """获取构件形式选项"""
        try:
            # 查询条件
            conditions = [
                Paths.bridge_type_id == bridge_type_id,
                Paths.part_id == part_id,
                Paths.component_form_id.is_not(None),
                Paths.is_active == True,
            ]

            # 处理结构类型条件
            if structure_id is not None:
                conditions.append(Paths.structure_id == structure_id)
            else:
                conditions.append(Paths.structure_id.is_(None))

            # 处理部件类型条件
            if component_type_id is not None:
                conditions.append(Paths.component_type_id == component_type_id)
            else:
                conditions.append(Paths.component_type_id.is_(None))

            existing_component_form_ids_stmt = (
                select(Paths.component_form_id).where(and_(*conditions)).distinct()
            )
            existing_ids = self.session.exec(existing_component_form_ids_stmt).all()

            if not existing_ids:
                return []

            # 查询构件形式详细信息
            stmt = (
                select(BridgeComponentForms.id, BridgeComponentForms.name)
                .where(
                    and_(
                        BridgeComponentForms.id.in_(existing_ids),
                        BridgeComponentForms.is_active == True,
                    )
                )
                .order_by(BridgeComponentForms.name)
            )

            results = self.session.exec(stmt).all()
            return [{"id": r[0], "name": r[1]} for r in results]

        except Exception as e:
            print(f"获取构件形式选项时出错: {e}")
            return []

    def create(self, obj_in: UserPathsCreate) -> UserPathsResponse:
        """
        创建用户路径

        Args:
            obj_in: 用户路径创建数据

        Returns:
            创建的用户路径响应
        """
        try:
            # 验证并查找对应的基础路径ID
            paths_id = self._find_matching_paths_id(obj_in)
            if not paths_id:
                raise ValidationException(
                    "未找到匹配的基础路径，请检查选择的路径组合是否正确"
                )

            # 检查实例名称是否重复
            self._check_instance_name_duplicate(
                obj_in.bridge_instance_name, obj_in.user_id
            )

            # 创建用户路径记录
            user_path = UserPaths(
                user_id=obj_in.user_id,
                bridge_instance_name=obj_in.bridge_instance_name,
                assessment_unit_instance_name=obj_in.assessment_unit_instance_name,
                category_id=obj_in.category_id,
                assessment_unit_id=obj_in.assessment_unit_id,
                bridge_type_id=obj_in.bridge_type_id,
                part_id=obj_in.part_id,
                structure_id=obj_in.structure_id,
                component_type_id=obj_in.component_type_id,
                component_form_id=obj_in.component_form_id,
                paths_id=paths_id,
                is_active=True,
            )

            self.session.add(user_path)
            self.session.commit()
            self.session.refresh(user_path)

            return self._get_user_path_with_details(user_path.id)

        except ValidationException:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"创建用户路径失败: {str(e)}")

    def _find_matching_paths_id(self, obj_in: UserPathsCreate) -> Optional[int]:
        """查找匹配的基础路径ID"""
        try:
            # 查询条件
            conditions = [
                Paths.category_id == obj_in.category_id,
                Paths.bridge_type_id == obj_in.bridge_type_id,
                Paths.part_id == obj_in.part_id,
                Paths.is_active == True,
            ]

            # 用户传入null，则查找名称为"-"的记录ID
            assessment_unit_id = obj_in.assessment_unit_id
            if assessment_unit_id is None:
                # 查找名称为"-"的评定单元ID
                assessment_unit_id = self._get_default_id(AssessmentUnit)
            conditions.append(Paths.assessment_unit_id == assessment_unit_id)

            structure_id = obj_in.structure_id
            if structure_id is None:
                # 查找名称为"-"的结构类型ID
                structure_id = self._get_default_id(BridgeStructures)
            conditions.append(Paths.structure_id == structure_id)

            component_type_id = obj_in.component_type_id
            if component_type_id is None:
                # 查找名称为"-"的部件类型ID
                component_type_id = self._get_default_id(BridgeComponentTypes)
            conditions.append(Paths.component_type_id == component_type_id)

            component_form_id = obj_in.component_form_id
            if component_form_id is None:
                # 查找名称为"-"的构件形式ID
                component_form_id = self._get_default_id(BridgeComponentForms)
            conditions.append(Paths.component_form_id == component_form_id)

            # 查询匹配的路径
            stmt = select(Paths.id).where(and_(*conditions)).limit(1)
            result = self.session.exec(stmt).first()

            return result

        except Exception as e:
            print(f"查找匹配路径时出错: {e}")
            return None

    def _get_default_id(self, model_class) -> Optional[int]:
        """获取名称为"-"的记录ID"""
        try:
            stmt = (
                select(model_class.id)
                .where(and_(model_class.name == "-", model_class.is_active == True))
                .limit(1)
            )
            result = self.session.exec(stmt).first()
            return result
        except Exception as e:
            print(f"获取默认ID时出错 {model_class.__name__}: {e}")
            return None

    def _check_instance_name_duplicate(
        self, instance_name: str, user_id: Optional[int]
    ):
        """检查实例名称是否重复"""
        try:
            conditions = [
                UserPaths.bridge_instance_name == instance_name,
                UserPaths.is_active == True,
            ]

            # 根据用户 id 来检查记录
            if user_id is not None:
                conditions.append(UserPaths.user_id == user_id)
            else:
                # 管理员
                conditions.append(UserPaths.user_id.is_(None))

            stmt = select(UserPaths.id).where(and_(*conditions)).limit(1)
            existing = self.session.exec(stmt).first()

            if existing:
                raise ValidationException(f"实例名称 '{instance_name}' 已存在")

        except ValidationException:
            raise
        except Exception as e:
            print(f"检查实例名称重复时出错: {e}")

    def _get_user_path_with_details(self, user_path_id: int) -> UserPathsResponse:
        """获取包含详细信息的用户路径"""
        try:
            # 查询用户路径记录
            stmt = select(UserPaths).where(
                and_(UserPaths.id == user_path_id, UserPaths.is_active == True)
            )
            user_path = self.session.exec(stmt).first()

            if not user_path:
                raise NotFoundException(
                    resource="UserPaths", identifier=str(user_path_id)
                )

            # 获取关联的详细信息
            details = self._get_related_names(user_path)

            return UserPathsResponse(
                id=user_path.id,
                user_id=user_path.user_id,
                bridge_instance_name=user_path.bridge_instance_name,
                assessment_unit_instance_name=user_path.assessment_unit_instance_name,
                category_id=user_path.category_id,
                category_name=details.get("category_name"),
                assessment_unit_id=user_path.assessment_unit_id,
                assessment_unit_name=details.get("assessment_unit_name"),
                bridge_type_id=user_path.bridge_type_id,
                bridge_type_name=details.get("bridge_type_name"),
                part_id=user_path.part_id,
                part_name=details.get("part_name"),
                structure_id=user_path.structure_id,
                structure_name=details.get("structure_name"),
                component_type_id=user_path.component_type_id,
                component_type_name=details.get("component_type_name"),
                component_form_id=user_path.component_form_id,
                component_form_name=details.get("component_form_name"),
                paths_id=user_path.paths_id,
                is_active=user_path.is_active,
                created_at=user_path.created_at,
                updated_at=user_path.updated_at,
            )

        except NotFoundException:
            raise
        except Exception as e:
            raise Exception(f"获取用户路径详情失败: {str(e)}")

    def _get_related_names(self, user_path: UserPaths) -> Dict[str, Optional[str]]:
        """获取关联表的名称信息"""
        details = {}

        # 映射关系
        field_mappings = [
            ("category_id", Categories, "category_name"),
            ("assessment_unit_id", AssessmentUnit, "assessment_unit_name"),
            ("bridge_type_id", BridgeTypes, "bridge_type_name"),
            ("part_id", BridgeParts, "part_name"),
            ("structure_id", BridgeStructures, "structure_name"),
            ("component_type_id", BridgeComponentTypes, "component_type_name"),
            ("component_form_id", BridgeComponentForms, "component_form_name"),
        ]

        for field_name, model_class, detail_key in field_mappings:
            field_id = getattr(user_path, field_name, None)
            if field_id:
                try:
                    stmt = select(model_class.name).where(model_class.id == field_id)
                    result = self.session.exec(stmt).first()
                    details[detail_key] = result
                except:
                    details[detail_key] = None
            else:
                details[detail_key] = None

        return details

    def update(self, user_path_id: int, obj_in: UserPathsUpdate) -> UserPathsResponse:
        """
        更新用户路径

        Args:
            user_path_id: 用户路径ID
            obj_in: 用户路径更新数据

        Returns:
            更新后的用户路径响应
        """
        try:
            # 查询现有记录
            existing_user_path = self.get_by_id(user_path_id)
            if not existing_user_path:
                raise NotFoundException(
                    resource="UserPaths", identifier=str(user_path_id)
                )

            # 获取更新数据
            update_data = obj_in.model_dump(exclude_unset=True)

            # 检查实例名称重复
            if "bridge_instance_name" in update_data:
                new_instance_name = update_data["bridge_instance_name"]
                if new_instance_name != existing_user_path.bridge_instance_name:
                    self._check_instance_name_duplicate_for_update(
                        new_instance_name, existing_user_path.user_id, user_path_id
                    )

            # 检查是否需要重新查找基础路径ID
            path_fields_changed = any(
                field in update_data
                for field in [
                    "category_id",
                    "assessment_unit_id",
                    "bridge_type_id",
                    "part_id",
                    "structure_id",
                    "component_type_id",
                    "component_form_id",
                ]
            )

            if path_fields_changed:
                # 构建新的路径数据
                new_path_data = UserPathsCreate(
                    category_id=update_data.get(
                        "category_id", existing_user_path.category_id
                    ),
                    assessment_unit_id=update_data.get(
                        "assessment_unit_id", existing_user_path.assessment_unit_id
                    ),
                    bridge_type_id=update_data.get(
                        "bridge_type_id", existing_user_path.bridge_type_id
                    ),
                    part_id=update_data.get("part_id", existing_user_path.part_id),
                    structure_id=update_data.get(
                        "structure_id", existing_user_path.structure_id
                    ),
                    component_type_id=update_data.get(
                        "component_type_id", existing_user_path.component_type_id
                    ),
                    component_form_id=update_data.get(
                        "component_form_id", existing_user_path.component_form_id
                    ),
                    user_id=existing_user_path.user_id,
                    bridge_instance_name=update_data.get(
                        "bridge_instance_name", existing_user_path.bridge_instance_name
                    ),
                    assessment_unit_instance_name=update_data.get(
                        "assessment_unit_instance_name",
                        existing_user_path.assessment_unit_instance_name,
                    ),
                )

                # 查找新的基础路径ID
                new_paths_id = self._find_matching_paths_id(new_path_data)
                if not new_paths_id:
                    raise ValidationException(
                        "未找到匹配的基础路径，请检查选择的路径组合是否正确"
                    )

                update_data["paths_id"] = new_paths_id

            # 更新记录
            for field, value in update_data.items():
                if hasattr(existing_user_path, field):
                    setattr(existing_user_path, field, value)

            existing_user_path.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            self.session.refresh(existing_user_path)

            return self._get_user_path_with_details(user_path_id)

        except (NotFoundException, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"更新用户路径失败: {str(e)}")

    def _check_instance_name_duplicate_for_update(
        self, instance_name: str, user_id: Optional[int], exclude_id: int
    ):
        """检查更新时实例名称是否重复"""
        try:
            conditions = [
                UserPaths.bridge_instance_name == instance_name,
                UserPaths.is_active == True,
                UserPaths.id != exclude_id,  # 排除当前记录
            ]

            # 根据用户 id 来检查记录
            if user_id is not None:
                conditions.append(UserPaths.user_id == user_id)
            else:
                conditions.append(UserPaths.user_id.is_(None))

            stmt = select(UserPaths.id).where(and_(*conditions)).limit(1)
            existing = self.session.exec(stmt).first()

            if existing:
                raise ValidationException(f"实例名称 '{instance_name}' 已存在")

        except ValidationException:
            raise
        except Exception as e:
            print(f"检查实例名称重复时出错: {e}")


def get_user_paths_service(session: Session) -> UserPathsService:
    """获取用户路径服务实例"""
    return UserPathsService(session)
