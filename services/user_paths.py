from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, and_
from datetime import datetime, timezone

from models import (
    Categories,
    BridgeTypes,
    BridgeParts,
    BridgeStructures,
    BridgeComponentTypes,
    BridgeComponentForms,
    Paths,
    AssessmentUnit,
    UserPaths,
)
from schemas import (
    UserPathsCreate,
    UserPathsUpdate,
    UserPathsResponse,
    CascadeOptionsRequest,
    CascadeOptionsResponse,
    NestedPathNode,
    PathValidationRequest,
)
from services import BaseCRUDService, PageParams, get_inspection_records_service
from exceptions import NotFoundException, ValidationException, DuplicateException
from utils import CascadeOptionsManager


class UserPathsService(BaseCRUDService[UserPaths, UserPathsCreate, UserPathsUpdate]):
    """用户路径服务类"""

    def __init__(self, session: Session):
        super().__init__(UserPaths, session)
        self.cascade_manager = CascadeOptionsManager(session)

    def get_cascade_options(
        self, request: CascadeOptionsRequest
    ) -> CascadeOptionsResponse:
        try:
            conditions = {
                "category_id": request.category_id,
                "assessment_unit_id": request.assessment_unit_id,
                "bridge_type_id": request.bridge_type_id,
                "part_id": request.part_id,
                "structure_id": request.structure_id,
                "component_type_id": request.component_type_id,
            }

            # 级联层级顺序
            cascade_levels = [
                "category",
                "assessment_unit",
                "bridge_type",
                "part",
                "structure",
                "component_type",
                "component_form",
            ]

            results = {}
            actual_conditions = {}

            for i, level in enumerate(cascade_levels):
                # 获取当前层级的选项
                parent_conditions = {
                    k: v for k, v in actual_conditions.items() if v is not None
                }

                raw_options = self.cascade_manager.get_cascade_options(
                    level, parent_conditions
                )
                processed_options, null_id = (
                    self.cascade_manager.process_cascade_result(raw_options)
                )

                results[f"{level}_options"] = processed_options

                # 更新下一层级
                current_value = conditions.get(f"{level}_id")

                if current_value is not None:
                    # 处理下一层级
                    actual_conditions[f"{level}_id"] = current_value
                elif null_id is not None:
                    # 当前层级只有"-"选项，使用null_id作为下级查询条件处理下一层级
                    actual_conditions[f"{level}_id"] = null_id
                else:
                    # 当前层级有多个选项但用户未选择，或者当前层级为空
                    # 停止处理后续层级，将剩余层级的选项设为空数组
                    for remaining_level in cascade_levels[i + 1 :]:
                        results[f"{remaining_level}_options"] = []
                    break

            return CascadeOptionsResponse(
                category_options=results["category_options"],
                assessment_unit_options=results["assessment_unit_options"],
                bridge_type_options=results["bridge_type_options"],
                part_options=results["part_options"],
                structure_options=results["structure_options"],
                component_type_options=results["component_type_options"],
                component_form_options=results["component_form_options"],
            )

        except Exception as e:
            print(f"获取级联选项时出错: {e}")
            raise Exception(f"获取级联选项失败: {str(e)}")

    def _check_duplicate_user_path(
        self, obj_in: UserPathsCreate, paths_id: int, exclude_id: Optional[int] = None
    ) -> None:
        """
        检查同一用户是否已创建相同路径

        Args:
            obj_in: 用户路径数据
            exclude_id: 排除的用户路径ID（用于更新时排除当前记录）

        Raises:
            DuplicateException: 当检测到重复路径时抛出
        """
        try:
            conditions = [
                UserPaths.user_id == obj_in.user_id,
                UserPaths.bridge_instance_name == obj_in.bridge_instance_name,
                UserPaths.paths_id == paths_id,
                UserPaths.is_active == True,
            ]

            if obj_in.assessment_unit_instance_name is not None:
                conditions.append(
                    UserPaths.assessment_unit_instance_name
                    == obj_in.assessment_unit_instance_name
                )
            else:
                conditions.append(UserPaths.assessment_unit_instance_name.is_(None))

            # 如果是更新操作，排除当前记录
            if exclude_id is not None:
                conditions.append(UserPaths.id != exclude_id)

            stmt = select(UserPaths).where(and_(*conditions)).limit(1)
            existing_path = self.session.exec(stmt).first()

            if existing_path:
                print(
                    f"发现重复路径，用户ID: {obj_in.user_id}, 桥梁: {obj_in.bridge_instance_name}"
                )
                raise ValidationException("该用户已创建相同的路径组合")

        except (ValidationException, DuplicateException):
            raise
        except Exception as e:
            print(f"检查重复用户路径时出错: {e}")
            raise Exception(f"检查重复路径失败: {str(e)}")

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

            # 如果用户不传评定单元id，则不能填写评定单元实例名称
            if not obj_in.assessment_unit_id and obj_in.assessment_unit_instance_name:
                raise ValidationException("评定单元实例名称不能填写，请选择评定单元")

            # 检查同一用户是否已创建相同路径
            self._check_duplicate_user_path(obj_in, paths_id=paths_id)

            # 创建用户路径记录
            user_path = UserPaths(
                user_id=obj_in.user_id,
                bridge_instance_name=obj_in.bridge_instance_name,
                assessment_unit_instance_name=obj_in.assessment_unit_instance_name,
                paths_id=paths_id,
                is_active=True,
            )

            self.session.add(user_path)
            self.session.commit()
            self.session.refresh(user_path)

            return self._get_user_path_with_details(user_path.id)

        except (ValidationException, DuplicateException):
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

            return UserPathsResponse(
                id=user_path.id,
                user_id=user_path.user_id,
                bridge_instance_name=user_path.bridge_instance_name,
                assessment_unit_instance_name=user_path.assessment_unit_instance_name,
                paths_id=user_path.paths_id,
                is_active=user_path.is_active,
                created_at=user_path.created_at,
                updated_at=user_path.updated_at,
            )

        except NotFoundException:
            raise
        except Exception as e:
            raise Exception(f"获取用户路径详情失败: {str(e)}")

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

            # 有基础路径字段更新，需要重新计算paths_id
            path_fields = [
                "category_id",
                "assessment_unit_id",
                "bridge_type_id",
                "part_id",
                "structure_id",
                "component_type_id",
                "component_form_id",
            ]

            if any(field in update_data for field in path_fields):
                # 获取当前paths记录的基础路径信息
                current_paths_stmt = select(Paths).where(
                    and_(
                        Paths.id == existing_user_path.paths_id, Paths.is_active == True
                    )
                )
                current_paths = self.session.exec(current_paths_stmt).first()

                if not current_paths:
                    raise ValidationException("当前用户路径关联的基础路径不存在")

                # 构建完整的路径数据用于查找新的paths_id
                merged_data = UserPathsCreate(
                    category_id=update_data.get(
                        "category_id", current_paths.category_id
                    ),
                    assessment_unit_id=update_data.get(
                        "assessment_unit_id", current_paths.assessment_unit_id
                    ),
                    bridge_type_id=update_data.get(
                        "bridge_type_id", current_paths.bridge_type_id
                    ),
                    part_id=update_data.get("part_id", current_paths.part_id),
                    structure_id=update_data.get(
                        "structure_id", current_paths.structure_id
                    ),
                    component_type_id=update_data.get(
                        "component_type_id", current_paths.component_type_id
                    ),
                    component_form_id=update_data.get(
                        "component_form_id", current_paths.component_form_id
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
                new_paths_id = self._find_matching_paths_id(merged_data)
                if not new_paths_id:
                    raise ValidationException(
                        "未找到匹配的基础路径，请检查选择的路径组合是否正确"
                    )

                # 检查用户路径是否重复
                self._check_duplicate_user_path(
                    merged_data, exclude_id=user_path_id, paths_id=new_paths_id
                )

                # 更新paths_id
                update_data["paths_id"] = new_paths_id

            # 验证评定单元实例名称逻辑
            final_assessment_unit_id = update_data.get("assessment_unit_id")
            final_assessment_unit_instance_name = update_data.get(
                "assessment_unit_instance_name"
            )

            if final_assessment_unit_id is None and final_assessment_unit_instance_name:
                raise ValidationException("评定单元实例名称不能填写，请选择评定单元")

            # 更新字段
            allowed_fields = {
                "bridge_instance_name",
                "assessment_unit_instance_name",
                "paths_id",
            }
            filtered_update_data = {
                k: v for k, v in update_data.items() if k in allowed_fields
            }

            # 更新
            for field, value in filtered_update_data.items():
                setattr(existing_user_path, field, value)

            existing_user_path.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            self.session.refresh(existing_user_path)

            return self._get_user_path_with_details(user_path_id)

        except (NotFoundException, ValidationException, DuplicateException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"更新用户路径失败: {str(e)}")

    def delete(self, user_path_id: int) -> bool:
        """
        删除用户路径

        Args:
            user_path_id: 用户路径ID

        Returns:
            删除是否成功

        Raises:
            NotFoundException: 用户路径不存在
            Exception: 删除失败
        """
        try:
            # 查询用户路径记录
            existing_user_path = self.get_by_id(user_path_id)
            if not existing_user_path:
                raise NotFoundException(
                    resource="UserPaths", identifier=str(user_path_id)
                )

            # 级联删除检查记录
            path_request = PathValidationRequest(
                user_id=existing_user_path.user_id,
                bridge_instance_name=existing_user_path.bridge_instance_name,
                assessment_unit_instance_name=existing_user_path.assessment_unit_instance_name,
                bridge_type_id=existing_user_path.bridge_type_id,
                part_id=existing_user_path.part_id,
                structure_id=existing_user_path.structure_id,
                component_type_id=existing_user_path.component_type_id,
                component_form_id=existing_user_path.component_form_id,
            )
            inspection_service = get_inspection_records_service(self.session)

            # 删除条件
            filters = {
                "bridge_instance_name": path_request.bridge_instance_name,
                "bridge_type_id": path_request.bridge_type_id,
                "part_id": path_request.part_id,
                "component_type_id": path_request.component_type_id,
                "component_form_id": path_request.component_form_id,
            }

            # 用户ID过滤
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

            # 批量软删除检查记录
            deleted_records_count = inspection_service.delete_all(filters)

            # 软删除用户路径
            existing_user_path.is_active = False
            existing_user_path.updated_at = datetime.now(timezone.utc)

            self.session.commit()

            print(
                f"成功删除用户路径 ID: {user_path_id}, 级联删除检查记录: {deleted_records_count} 条"
            )

            return True

        except NotFoundException:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"删除用户路径失败: {str(e)}")

    def get_nested_user_paths_data(
        self, user_id: Optional[int] = None
    ) -> List[NestedPathNode]:
        """
        获取用户路径的嵌套数据结构

        Args:
            user_id: 用户ID（可选，为空返回所有用户数据）

        Returns:
            嵌套结构数据，顶层是类别，然后是实例桥，评定单元，实例单元，桥类型等
        """
        try:
            conditions = [UserPaths.is_active == True]

            if user_id is not None:
                conditions.append(UserPaths.user_id == user_id)

            stmt = select(UserPaths).where(and_(*conditions))
            user_paths = self.session.exec(stmt).all()

            if not user_paths:
                return []

            return self._build_complete_nested_structure(user_paths)

        except Exception as e:
            print(f"获取嵌套用户路径数据时出错: {e}")
            raise Exception(f"获取嵌套用户路径数据失败: {str(e)}")

    def _build_complete_nested_structure(
        self, user_paths: List[UserPaths]
    ) -> List[NestedPathNode]:
        """
        构建完整的嵌套数据结构
        层级顺序：类别 -> 实例桥 -> 评定单元 -> 实例单元 -> 桥类型 -> 部位 -> 结构类型 -> 部件类型 -> 构件形式

        Args:
            user_paths: 用户路径数据列表

        Returns:
            完整的嵌套结构
        """
        try:
            # 按类别分组
            category_groups = {}
            for path in user_paths:
                if path.category_id not in category_groups:
                    category_groups[path.category_id] = []
                category_groups[path.category_id].append(path)

            # 类别层级
            category_nodes = []
            for category_id, category_paths in category_groups.items():
                category_data = self._get_single_category_data(category_id)
                if not category_data:
                    continue

                # 实例桥层级
                bridge_instance_children = self._build_bridge_instance_level(
                    category_paths
                )

                category_node = NestedPathNode(
                    id=category_id,
                    name=category_data["name"],
                    level="category",
                    children=(
                        bridge_instance_children if bridge_instance_children else None
                    ),
                )
                category_nodes.append(category_node)

            return category_nodes

        except Exception as e:
            print(f"构建完整嵌套结构时出错: {e}")
            return []

    def _build_bridge_instance_level(
        self, user_paths: List[UserPaths]
    ) -> List[NestedPathNode]:
        """实例桥层级"""
        # 按实例桥名称分组
        bridge_groups = {}
        for path in user_paths:
            bridge_name = path.bridge_instance_name
            if bridge_name not in bridge_groups:
                bridge_groups[bridge_name] = []
            bridge_groups[bridge_name].append(path)

        bridge_nodes = []
        for bridge_name, bridge_paths in bridge_groups.items():
            # 评定单元层级
            assessment_unit_children = self._build_assessment_unit_level(bridge_paths)

            bridge_node = NestedPathNode(
                id=None,  # 实例桥没有ID
                name=bridge_name,
                level="bridge_instance",
                children=assessment_unit_children if assessment_unit_children else None,
            )
            bridge_nodes.append(bridge_node)

        return bridge_nodes

    def _build_assessment_unit_level(
        self, user_paths: List[UserPaths]
    ) -> List[NestedPathNode]:
        """评定单元层级，过滤掉'-'的数据"""
        # 按评定单元分组
        assessment_unit_groups = {}
        for path in user_paths:
            unit_id = path.assessment_unit_id
            unit_name = path.assessment_unit_instance_name

            # 获取评定单元的标准名称
            if unit_id:
                standard_name_data = self._get_single_assessment_unit_data(unit_id)
                standard_name = (
                    standard_name_data["name"] if standard_name_data else None
                )

                # 过滤掉名称为"-"的评定单元
                if standard_name and standard_name != "-":
                    key = (unit_id, unit_name)
                    if key not in assessment_unit_groups:
                        assessment_unit_groups[key] = {
                            "standard_name": standard_name,
                            "paths": [],
                        }
                    assessment_unit_groups[key]["paths"].append(path)

        # 如果所有评定单元都是"-"，则跳过这一层，直接构建桥类型层级
        if not assessment_unit_groups:
            return self._build_bridge_type_level(user_paths)

        unit_nodes = []
        for (unit_id, unit_instance_name), unit_data in assessment_unit_groups.items():
            # 实例单元层级
            instance_unit_children = self._build_instance_unit_level(unit_data["paths"])

            display_name = (
                unit_instance_name if unit_instance_name else unit_data["standard_name"]
            )

            unit_node = NestedPathNode(
                id=unit_id,
                name=display_name,
                level="assessment_unit",
                children=instance_unit_children if instance_unit_children else None,
            )
            unit_nodes.append(unit_node)

        return unit_nodes

    def _build_instance_unit_level(
        self, user_paths: List[UserPaths]
    ) -> List[NestedPathNode]:
        """实例单元层级"""
        # 按实例单元名称分组
        instance_groups = {}
        for path in user_paths:
            instance_name = path.assessment_unit_instance_name or "默认实例单元"
            if instance_name not in instance_groups:
                instance_groups[instance_name] = []
            instance_groups[instance_name].append(path)

        instance_nodes = []
        for instance_name, instance_paths in instance_groups.items():
            # 桥类型层级
            bridge_type_children = self._build_bridge_type_level(instance_paths)

            instance_node = NestedPathNode(
                id=None,
                name=instance_name,
                level="instance_unit",
                children=bridge_type_children if bridge_type_children else None,
            )
            instance_nodes.append(instance_node)

        return instance_nodes

    def _build_bridge_type_level(
        self, user_paths: List[UserPaths]
    ) -> List[NestedPathNode]:
        """桥类型层级，过滤掉'-'的数据"""
        # 按桥类型分组
        bridge_type_groups = {}
        for path in user_paths:
            type_id = path.bridge_type_id
            if type_id and type_id not in bridge_type_groups:
                bridge_type_groups[type_id] = []
            if type_id:
                bridge_type_groups[type_id].append(path)

        type_nodes = []
        for type_id, type_paths in bridge_type_groups.items():
            type_data = self._get_single_bridge_type_data(type_id)
            if not type_data or type_data["name"] == "-":
                # 如果桥类型为"-"，跳过该层级，直接构建下一层
                type_nodes.extend(self._build_remaining_levels(type_paths))
                continue

            # 剩余层级
            remaining_children = self._build_remaining_levels(type_paths)

            type_node = NestedPathNode(
                id=type_id,
                name=type_data["name"],
                level="bridge_type",
                children=remaining_children if remaining_children else None,
            )
            type_nodes.append(type_node)

        return type_nodes

    def _build_remaining_levels(
        self, user_paths: List[UserPaths]
    ) -> List[NestedPathNode]:
        """
        构建剩余的层级（部位 -> 结构类型 -> 部件类型 -> 构件形式）
        按照原有的递归逻辑，过滤掉'-'的数据
        """
        level_hierarchy = [
            ("part", self._get_part_data_for_remaining),
            ("structure", self._get_structure_data_for_remaining),
            ("component_type", self._get_component_type_data_for_remaining),
            ("component_form", self._get_component_form_data_for_remaining),
        ]

        return self._build_level_nodes_for_remaining(user_paths, level_hierarchy, 0)

    def _build_level_nodes_for_remaining(
        self,
        user_paths: List[UserPaths],
        level_hierarchy: List[tuple],
        current_level: int,
    ) -> List[NestedPathNode]:
        """
        递归剩余层级的节点
        """
        if current_level >= len(level_hierarchy) or not user_paths:
            return []

        level_name, data_getter = level_hierarchy[current_level]

        # 获取当前层级的唯一数据
        unique_items = data_getter(user_paths)

        # 过滤掉 name 为 "-" 的项目
        filtered_items = [item for item in unique_items if item.get("name") != "-"]

        # 如果当前层级没有有效数据，跳到下一层级
        if not filtered_items:
            return self._build_level_nodes_for_remaining(
                user_paths, level_hierarchy, current_level + 1
            )

        nodes = []
        for item in filtered_items:
            # 获取属于当前项目的用户路径数据
            filtered_paths = self._filter_paths_by_level_for_remaining(
                user_paths, level_name, item["id"]
            )

            # 递归构建子节点
            children = self._build_level_nodes_for_remaining(
                filtered_paths, level_hierarchy, current_level + 1
            )

            node = NestedPathNode(
                id=item["id"],
                name=item["name"],
                level=level_name,
                children=children if children else None,
            )
            nodes.append(node)

        return nodes

    def _filter_paths_by_level_for_remaining(
        self, user_paths: List[UserPaths], level: str, item_id: int
    ) -> List[UserPaths]:
        """
        根据层级和ID过滤用户路径数据
        """
        level_field_mapping = {
            "part": "part_id",
            "structure": "structure_id",
            "component_type": "component_type_id",
            "component_form": "component_form_id",
        }

        field_name = level_field_mapping.get(level)
        if not field_name:
            return []

        return [path for path in user_paths if getattr(path, field_name) == item_id]

    def _get_single_category_data(self, category_id: int) -> Optional[Dict[str, Any]]:
        """获取单个类别数据"""
        try:
            stmt = select(Categories.id, Categories.name).where(
                and_(Categories.id == category_id, Categories.is_active == True)
            )
            result = self.session.exec(stmt).first()
            return {"id": result[0], "name": result[1]} if result else None
        except Exception:
            return None

    def _get_single_assessment_unit_data(
        self, unit_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取单个评定单元数据"""
        try:
            stmt = select(AssessmentUnit.id, AssessmentUnit.name).where(
                and_(AssessmentUnit.id == unit_id, AssessmentUnit.is_active == True)
            )
            result = self.session.exec(stmt).first()
            return {"id": result[0], "name": result[1]} if result else None
        except Exception:
            return None

    def _get_single_bridge_type_data(self, type_id: int) -> Optional[Dict[str, Any]]:
        """获取单个桥类型数据"""
        try:
            stmt = select(BridgeTypes.id, BridgeTypes.name).where(
                and_(BridgeTypes.id == type_id, BridgeTypes.is_active == True)
            )
            result = self.session.exec(stmt).first()
            return {"id": result[0], "name": result[1]} if result else None
        except Exception:
            return None

    # 剩余层级
    def _get_part_data_for_remaining(
        self, user_paths: List[UserPaths]
    ) -> List[Dict[str, Any]]:
        """获取部位数据"""
        unique_ids = list(set([path.part_id for path in user_paths if path.part_id]))
        if not unique_ids:
            return []

        stmt = (
            select(BridgeParts.id, BridgeParts.name)
            .where(and_(BridgeParts.id.in_(unique_ids), BridgeParts.is_active == True))
            .order_by(BridgeParts.name)
        )

        results = self.session.exec(stmt).all()
        return [{"id": r[0], "name": r[1]} for r in results]

    def _get_structure_data_for_remaining(
        self, user_paths: List[UserPaths]
    ) -> List[Dict[str, Any]]:
        """获取结构类型数据"""
        unique_ids = list(
            set([path.structure_id for path in user_paths if path.structure_id])
        )
        if not unique_ids:
            return []

        stmt = (
            select(BridgeStructures.id, BridgeStructures.name)
            .where(
                and_(
                    BridgeStructures.id.in_(unique_ids),
                    BridgeStructures.is_active == True,
                )
            )
            .order_by(BridgeStructures.name)
        )

        results = self.session.exec(stmt).all()
        return [{"id": r[0], "name": r[1]} for r in results]

    def _get_component_type_data_for_remaining(
        self, user_paths: List[UserPaths]
    ) -> List[Dict[str, Any]]:
        """获取部件类型数"""
        unique_ids = list(
            set(
                [
                    path.component_type_id
                    for path in user_paths
                    if path.component_type_id
                ]
            )
        )
        if not unique_ids:
            return []

        stmt = (
            select(BridgeComponentTypes.id, BridgeComponentTypes.name)
            .where(
                and_(
                    BridgeComponentTypes.id.in_(unique_ids),
                    BridgeComponentTypes.is_active == True,
                )
            )
            .order_by(BridgeComponentTypes.name)
        )

        results = self.session.exec(stmt).all()
        return [{"id": r[0], "name": r[1]} for r in results]

    def _get_component_form_data_for_remaining(
        self, user_paths: List[UserPaths]
    ) -> List[Dict[str, Any]]:
        """获取构件形式数据"""
        unique_ids = list(
            set(
                [
                    path.component_form_id
                    for path in user_paths
                    if path.component_form_id
                ]
            )
        )
        if not unique_ids:
            return []

        stmt = (
            select(BridgeComponentForms.id, BridgeComponentForms.name)
            .where(
                and_(
                    BridgeComponentForms.id.in_(unique_ids),
                    BridgeComponentForms.is_active == True,
                )
            )
            .order_by(BridgeComponentForms.name)
        )

        results = self.session.exec(stmt).all()
        return [{"id": r[0], "name": r[1]} for r in results]


def get_user_paths_service(session: Session) -> UserPathsService:
    """获取用户路径服务实例"""
    return UserPathsService(session)
