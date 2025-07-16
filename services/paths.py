from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, and_
from sqlalchemy import func

from models.paths import Paths
from schemas.paths import PathsCreate, PathsUpdate, PathConditions, PathsResponse
from services.base_crud import BaseCRUDService, PageParams
from models import (
    Categories,
    AssessmentUnit,
    BridgeTypes,
    BridgeParts,
    BridgeStructures,
    BridgeComponentTypes,
    BridgeComponentForms,
    BridgeDiseases,
    BridgeScales,
    BridgeQualities,
    BridgeQuantities,
)
from exceptions import DuplicateException, NotFoundException, ValidationException


# 需要自定义类，不能用工厂函数，只能继承
class PathsService(BaseCRUDService[Paths, PathsCreate, PathsUpdate]):
    """路径服务类"""

    def __init__(self, session: Session):
        super().__init__(Paths, session)

    def get_paths_with_pagination(
        self, page_params: PageParams, conditions: Optional[PathConditions] = None
    ) -> Tuple[List[PathsResponse], int]:
        """
        分页查询路径数据

        Args:
            page_params: 分页参数
            conditions: 查询条件

        Returns:
            (路径列表, 总数)
        """
        try:
            # 构建基础查询
            statement = select(Paths)
            count_statement = select(func.count(Paths.id))

            # 构建过滤条件
            filter_conditions = []
            if hasattr(Paths, "is_active"):
                filter_conditions.append(Paths.is_active == True)

            if conditions:
                filter_conditions.extend(self._build_path_filter_conditions(conditions))

            # 应用过滤条件
            if filter_conditions:
                statement = statement.where(and_(*filter_conditions))
                count_statement = count_statement.where(and_(*filter_conditions))

            # 排序
            statement = statement.order_by(Paths.id)

            # 分页
            statement = statement.offset(page_params.offset).limit(page_params.size)

            # 执行查询
            results = self.session.exec(statement).all()
            total = self.session.exec(count_statement).first() or 0

            # 转换为PathsResponse格式
            paths_list = []
            for result in results:
                path_data = {
                    "id": result.id,
                    "code": result.code,
                    "name": result.name,
                }

                # 添加各个ID对应的code和name
                path_data.update(self._get_related_codes_and_names(result))
                paths_list.append(PathsResponse(**path_data))

            return paths_list, total

        except Exception as e:
            print(f"分页查询路径数据时出错: {e}")
            return [], 0

    def _get_related_codes_and_names(self, path_result) -> Dict[str, Any]:
        """
        获取path记录中各个ID对应的code和name
        """
        related_data = {}

        # 定义字段映射关系
        field_mappings = [
            ("category_id", Categories, "category"),
            ("assessment_unit_id", AssessmentUnit, "assessment_unit"),
            ("bridge_type_id", BridgeTypes, "bridge_type"),
            ("part_id", BridgeParts, "part"),
            ("structure_id", BridgeStructures, "structure"),
            ("component_type_id", BridgeComponentTypes, "component_type"),
            ("component_form_id", BridgeComponentForms, "component_form"),
            ("disease_id", BridgeDiseases, "disease"),
            ("scale_id", BridgeScales, "scale"),
            ("quality_id", BridgeQualities, "quality"),
            ("quantity_id", BridgeQuantities, "quantity"),
        ]

        for field_name, model_class, prefix in field_mappings:
            field_id = getattr(path_result, field_name, None)
            if field_id:
                try:
                    stmt = select(model_class.code, model_class.name).where(
                        model_class.id == field_id
                    )
                    result = self.session.exec(stmt).first()
                    if result:
                        related_data[f"{prefix}_code"] = result[0]
                        related_data[f"{prefix}_name"] = result[1]
                    else:
                        related_data[f"{prefix}_code"] = None
                        related_data[f"{prefix}_name"] = None
                except Exception as e:
                    print(
                        f"查询模型 {model_class.__name__} 中ID为 {field_id} 的记录时出错: {e}"
                    )
                    related_data[f"{prefix}_code"] = None
                    related_data[f"{prefix}_name"] = None
            else:
                related_data[f"{prefix}_code"] = None
                related_data[f"{prefix}_name"] = None

        return related_data

    def get_filter_options(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取Paths 表中存在的所有相关表的code和name

        Returns:
            包含各表选项的字典
        """
        try:
            options = {}

            # 定义字段映射
            table_configs = [
                ("categories", Categories, "category", Paths.category_id),
                (
                    "assessment_units",
                    AssessmentUnit,
                    "assessment_unit",
                    Paths.assessment_unit_id,
                ),
                ("bridge_types", BridgeTypes, "bridge_type", Paths.bridge_type_id),
                ("bridge_parts", BridgeParts, "part", Paths.part_id),
                (
                    "bridge_structures",
                    BridgeStructures,
                    "structure",
                    Paths.structure_id,
                ),
                (
                    "bridge_component_types",
                    BridgeComponentTypes,
                    "component_type",
                    Paths.component_type_id,
                ),
                (
                    "bridge_component_forms",
                    BridgeComponentForms,
                    "component_form",
                    Paths.component_form_id,
                ),
                ("bridge_diseases", BridgeDiseases, "disease", Paths.disease_id),
                ("bridge_scales", BridgeScales, "scale", Paths.scale_id),
                ("bridge_qualities", BridgeQualities, "quality", Paths.quality_id),
                ("bridge_quantities", BridgeQuantities, "quantity", Paths.quantity_id),
            ]

            for table_name, model_class, option_key, path_field in table_configs:
                try:
                    # 查询在paths表中存在的ID
                    existing_ids_stmt = (
                        select(path_field).where(path_field.is_not(None)).distinct()
                    )
                    existing_ids = self.session.exec(existing_ids_stmt).all()

                    if existing_ids:
                        # 查询在paths表中存在的记录
                        stmt = (
                            select(model_class.code, model_class.name)
                            .where(
                                and_(
                                    model_class.id.in_(existing_ids),
                                    model_class.is_active == True,
                                )
                            )
                            .order_by(model_class.code)
                        )

                        result = self.session.exec(stmt).all()
                        options[option_key] = [
                            {"code": row[0], "name": row[1]} for row in result
                        ]
                    else:
                        options[option_key] = []

                except Exception as e:
                    print(f"查询表 {table_name} 选项时出错: {e}")
                    options[option_key] = []

            return options

        except Exception as e:
            print(f"获取过滤选项时出错: {e}")
            return {}

    def _build_path_filter_conditions(self, conditions: PathConditions) -> List[Any]:
        """
        构建路径查询过滤条件

        Args:
            conditions: 查询条件对象

        Returns:
            条件列表：[Paths.category_id == 3, Paths.bridge_type_id == 5]
        """
        filter_conditions = []

        try:
            # 按code过滤
            code_mappings = [
                # 前端传入category_code，对应基础表模型Categories，对比 Paths 表的 category_id 字段
                ("category_code", Categories, Paths.category_id),
                ("assessment_unit_code", AssessmentUnit, Paths.assessment_unit_id),
                ("bridge_type_code", BridgeTypes, Paths.bridge_type_id),
                ("part_code", BridgeParts, Paths.part_id),
                ("structure_code", BridgeStructures, Paths.structure_id),
                ("component_type_code", BridgeComponentTypes, Paths.component_type_id),
                ("component_form_code", BridgeComponentForms, Paths.component_form_id),
                ("disease_code", BridgeDiseases, Paths.disease_id),
                ("scale_code", BridgeScales, Paths.scale_id),
                ("quality_code", BridgeQualities, Paths.quality_id),
                ("quantity_code", BridgeQuantities, Paths.quantity_id),
            ]

            for condition_field, model_class, path_field in code_mappings:
                # 获取前端传入的code值
                code_value = getattr(conditions, condition_field, None)
                if code_value:
                    try:
                        # 找到对应的ID
                        stmt = select(model_class.id).where(
                            model_class.code == code_value
                        )
                        result = self.session.exec(stmt).first()
                        if result:
                            filter_conditions.append(path_field == result)
                    except Exception as e:
                        print(
                            f"查询 {model_class.__name__} 中code为 {code_value} 的记录时出错: {e}"
                        )

        except Exception as e:
            print(f"构建路径过滤条件时出错: {e}")

        return filter_conditions

    def get_options(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取所有相关表的 code、name 和 id

        Returns:
            包含各表选项的字典
        """
        all_options = {}

        # 定义基础表的映射关系
        table_configs = [
            ("categories", Categories, "category"),
            ("assessment_units", AssessmentUnit, "assessment_unit"),
            ("bridge_types", BridgeTypes, "bridge_type"),
            ("bridge_parts", BridgeParts, "part"),
            ("bridge_structures", BridgeStructures, "structure"),
            ("bridge_component_types", BridgeComponentTypes, "component_type"),
            ("bridge_component_forms", BridgeComponentForms, "component_form"),
            ("bridge_diseases", BridgeDiseases, "disease"),
            ("bridge_scales", BridgeScales, "scale"),
            ("bridge_qualities", BridgeQualities, "quality"),
            ("bridge_quantities", BridgeQuantities, "quantity"),
        ]

        for option_key, model_class, _ in table_configs:
            try:
                # 查询所有记录
                stmt = (
                    select(model_class.id, model_class.code, model_class.name)
                    .where(model_class.is_active == True)
                    .order_by(model_class.code)
                )
                results = self.session.exec(stmt).all()
                all_options[option_key] = [
                    {"id": row[0], "code": row[1], "name": row[2]} for row in results
                ]
            except Exception as e:
                print(f"查询表 {option_key} 选项时出错: {e}")
                all_options[option_key] = []

        return all_options

    def get_by_id_with_details(self, id: int) -> Optional[PathsResponse]:
        """根据 id 获取paths单条记录数据"""
        try:
            # 构建查询语句
            stmt = select(Paths).where(Paths.id == id)
            if hasattr(Paths, "is_active"):
                stmt = stmt.where(Paths.is_active == True)

            result = self.session.exec(stmt).first()

            if not result:
                return None

            # 构建基础数据
            path_data = {
                "id": result.id,
                "code": result.code,
                "name": result.name,
            }

            # 添加各个ID对应的code和name
            path_data.update(self._get_related_codes_and_names(result))

            return PathsResponse(**path_data)

        except Exception as e:
            print(f"获取paths单条记录数据时出错: {e}")
            return None

    def create(self, obj_in: PathsCreate) -> Optional[PathsResponse]:
        """
        创建paths记录

        Args:
            obj_in: 创建路径参数

        Returns:
            创建后的路径数据
        """
        try:
            # 1. 检查 code 和 name
            code_value = obj_in.code
            if not code_value or not code_value.strip():
                # 自动生成 code
                generated_code = self.code_generator.generate_code("paths")
                code_value = generated_code
            else:
                # 检查用户提供的 code 的唯一性
                existing_code = self.get_by_code(code_value.strip())
                if existing_code:

                    raise DuplicateException(
                        resource="Paths", field="code", value=code_value.strip()
                    )
                code_value = code_value.strip()

            if obj_in.name:
                stmt = select(Paths).where(Paths.name == obj_in.name)
                if hasattr(Paths, "is_active"):
                    stmt = stmt.where(Paths.is_active == True)
                existing_name = self.session.exec(stmt).first()
                if existing_name:
                    raise DuplicateException(
                        resource="Paths", field="name", value=obj_in.name
                    )

            # 2. 通过各种 code 找到对应的 ID
            path_data = {
                "code": code_value,
                "name": obj_in.name,
            }

            # 定义 code 到 ID 的映射关系
            code_to_id_mappings = [
                ("category_code", Categories, "category_id"),
                ("assessment_unit_code", AssessmentUnit, "assessment_unit_id"),
                ("bridge_type_code", BridgeTypes, "bridge_type_id"),
                ("part_code", BridgeParts, "part_id"),
                ("structure_code", BridgeStructures, "structure_id"),
                ("component_type_code", BridgeComponentTypes, "component_type_id"),
                ("component_form_code", BridgeComponentForms, "component_form_id"),
                ("disease_code", BridgeDiseases, "disease_id"),
                ("scale_code", BridgeScales, "scale_id"),
                ("quality_code", BridgeQualities, "quality_id"),
                ("quantity_code", BridgeQuantities, "quantity_id"),
            ]

            for code_field, model_class, id_field in code_to_id_mappings:
                code_value = getattr(obj_in, code_field, None)
                if code_value:
                    # 查找对应的 ID
                    stmt = select(model_class.id).where(
                        and_(
                            model_class.code == code_value,
                            model_class.is_active == True,
                        )
                    )
                    result = self.session.exec(stmt).first()
                    if result:
                        path_data[id_field] = result
                    else:
                        raise ValidationException(
                            f"找不到 {code_field} 为 '{code_value}' 的记录"
                        )

            # 3. 检查路径表记录的唯一性
            path_uniqueness_fields = [
                "category_id",
                "assessment_unit_id",
                "bridge_type_id",
                "part_id",
                "structure_id",
                "component_type_id",
                "component_form_id",
                "disease_id",
                "scale_id",
                "quality_id",
                "quantity_id",
            ]

            # 构建唯一性检查条件
            uniqueness_conditions = []
            for field in path_uniqueness_fields:
                field_value = path_data.get(field)
                if field_value is not None:
                    uniqueness_conditions.append(getattr(Paths, field) == field_value)
                else:
                    uniqueness_conditions.append(getattr(Paths, field).is_(None))

            # 检查是否存在完全相同的路径记录
            if uniqueness_conditions:
                stmt = select(Paths).where(and_(*uniqueness_conditions))
                if hasattr(Paths, "is_active"):
                    stmt = stmt.where(Paths.is_active == True)
                existing_path = self.session.exec(stmt).first()
                if existing_path:
                    raise DuplicateException(
                        resource="Paths",
                        field="path_combination",
                        value="相同的路径组合已存在",
                    )

            # 4. 创建记录
            path_model = Paths(**path_data)
            self.session.add(path_model)
            self.session.commit()
            self.session.refresh(path_model)

            # 5. 构建返回数据
            response_data = {
                "id": path_model.id,
                "code": path_model.code,
                "name": path_model.name,
            }

            # 添加各个ID对应的code和name
            response_data.update(self._get_related_codes_and_names(path_model))

            return PathsResponse(**response_data)

        except Exception as e:
            self.session.rollback()
            print(f"创建paths记录时出错: {e}")
            raise


def get_paths_service(session: Session) -> PathsService:
    """
    获取paths服务实例
    """
    return PathsService(session)
