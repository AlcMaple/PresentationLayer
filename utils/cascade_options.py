from typing import List, Optional, Dict, Any, Type, Tuple
from sqlmodel import Session, select, and_
from dataclasses import dataclass

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


@dataclass
class CascadeFieldConfig:
    """级联字段配置"""

    field_name: str  # 字段名，如 bridge_type_id
    model_class: Type  # 对应的模型类，如 BridgeTypes
    order_field: str = "name"  # 排序字段，默认按name排序


class CascadeOptionsProvider:
    """级联选项提供器"""

    def __init__(self, session: Session):
        self.session = session

    def get_options_from_paths(
        self,
        target_field: str,
        target_model: Type,
        conditions: Optional[Dict[str, Any]] = None,
        order_field: str = "name",
        filter_dash: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        从paths表获取级联选项的通用方法

        Args:
            target_field: 目标字段名，如 bridge_type_id
            target_model: 目标模型类，如 BridgeTypes
            conditions: 查询条件字典，如 {'bridge_type_id': 1}
            order_field: 排序字段，默认为 'name'
            filter_dash: 是否过滤掉名为"-"的记录

        Returns:
            选项列表，格式为 [{"id": id, "name": name}, ...]
        """
        try:
            path_conditions = [
                getattr(Paths, target_field).is_not(None),
                Paths.is_active == True,
            ]

            if conditions:
                for field_name, value in conditions.items():
                    if value is not None:
                        path_conditions.append(getattr(Paths, field_name) == value)
                    else:
                        path_conditions.append(getattr(Paths, field_name).is_(None))

            existing_ids_stmt = (
                select(getattr(Paths, target_field))
                .where(and_(*path_conditions))
                .distinct()
            )
            existing_ids = self.session.exec(existing_ids_stmt).all()

            if not existing_ids:
                return []

            target_conditions = [
                target_model.id.in_(existing_ids),
                target_model.is_active == True,
            ]

            stmt = (
                select(target_model.id, getattr(target_model, order_field))
                .where(and_(*target_conditions))
                .order_by(getattr(target_model, order_field))
            )

            results = self.session.exec(stmt).all()

            if filter_dash and len(results) > 1:
                return [{"id": r[0], "name": r[1]} for r in results if r[1] != "-"]

            return [{"id": r[0], "name": r[1]} for r in results]

        except Exception as e:
            print(f"获取{target_field}选项时出错: {e}")
            return []


class CascadeOptionsManager:
    """级联选项管理器"""

    def __init__(self, session: Session):
        self.session = session
        self.provider = CascadeOptionsProvider(session)

        # 定义级联字段配置
        self.cascade_configs = {
            "category": CascadeFieldConfig("category_id", Categories),
            "assessment_unit": CascadeFieldConfig("assessment_unit_id", AssessmentUnit),
            "bridge_type": CascadeFieldConfig("bridge_type_id", BridgeTypes),
            "part": CascadeFieldConfig("part_id", BridgeParts),
            "structure": CascadeFieldConfig("structure_id", BridgeStructures),
            "component_type": CascadeFieldConfig(
                "component_type_id", BridgeComponentTypes
            ),
            "component_form": CascadeFieldConfig(
                "component_form_id", BridgeComponentForms
            ),
        }

    def get_category_options(self) -> List[Dict[str, Any]]:
        """获取桥梁类别选项"""
        config = self.cascade_configs["category"]
        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            order_field=config.order_field,
        )

    def get_assessment_unit_options(
        self, category_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """获取评定单元选项"""
        if not category_id:
            return []

        config = self.cascade_configs["assessment_unit"]
        conditions = {"category_id": category_id}

        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            conditions=conditions,
            order_field=config.order_field,
        )

    def get_bridge_type_options(
        self, category_id: Optional[int], assessment_unit_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """获取桥梁类型选项"""
        if not category_id:
            return []

        config = self.cascade_configs["bridge_type"]
        conditions = {
            "category_id": category_id,
            "assessment_unit_id": assessment_unit_id,
        }

        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            conditions=conditions,
            order_field=config.order_field,
        )

    def get_part_options(
        self,
        category_id: Optional[int],
        assessment_unit_id: Optional[int],
        bridge_type_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        """获取部位选项"""
        if not category_id:
            return []

        config = self.cascade_configs["part"]
        conditions = {
            "category_id": category_id,
            "assessment_unit_id": assessment_unit_id,
            "bridge_type_id": bridge_type_id,
        }

        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            conditions=conditions,
            order_field=config.order_field,
        )

    def get_structure_options(
        self,
        category_id: Optional[int],
        assessment_unit_id: Optional[int],
        bridge_type_id: Optional[int],
        part_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        """获取结构类型选项"""
        if not category_id:
            return []

        config = self.cascade_configs["structure"]
        conditions = {
            "category_id": category_id,
            "assessment_unit_id": assessment_unit_id,
            "bridge_type_id": bridge_type_id,
            "part_id": part_id,
        }

        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            conditions=conditions,
            order_field=config.order_field,
        )

    def get_component_type_options(
        self,
        category_id: Optional[int],
        assessment_unit_id: Optional[int],
        bridge_type_id: Optional[int],
        part_id: Optional[int],
        structure_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        """获取部件类型选项"""
        if not category_id:
            return []

        config = self.cascade_configs["component_type"]
        conditions = {
            "category_id": category_id,
            "assessment_unit_id": assessment_unit_id,
            "bridge_type_id": bridge_type_id,
            "part_id": part_id,
            "structure_id": structure_id,
        }

        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            conditions=conditions,
            order_field=config.order_field,
        )

    def get_component_form_options(
        self,
        category_id: Optional[int],
        assessment_unit_id: Optional[int],
        bridge_type_id: Optional[int],
        part_id: Optional[int],
        structure_id: Optional[int],
        component_type_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        """获取构件形式选项"""
        if not category_id:
            return []

        config = self.cascade_configs["component_form"]
        conditions = {
            "category_id": category_id,
            "assessment_unit_id": assessment_unit_id,
            "bridge_type_id": bridge_type_id,
            "part_id": part_id,
            "structure_id": structure_id,
            "component_type_id": component_type_id,
        }

        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            conditions=conditions,
            order_field=config.order_field,
        )

    def get_cascade_options(
        self, level: str, parent_conditions: Dict[str, Optional[int]]
    ) -> List[Dict[str, Any]]:
        """
        级联选项获取方法

        Args:
            level: 级联层级名称，如 'category', 'assessment_unit', 'bridge_type' 等
            parent_conditions: 父级条件字典

        Returns:
            选项列表
        """
        if level not in self.cascade_configs:
            return []

        config = self.cascade_configs[level]

        # 第一层不需要条件
        if level == "category":
            return self.provider.get_options_from_paths(
                target_field=config.field_name,
                target_model=config.model_class,
                order_field=config.order_field,
            )

        # 其他层级检查父级条件
        if not parent_conditions.get("category_id"):
            return []

        return self.provider.get_options_from_paths(
            target_field=config.field_name,
            target_model=config.model_class,
            conditions=parent_conditions,
            order_field=config.order_field,
        )

    def process_cascade_result(
        self, options: List[Dict[str, Any]], request_id_field: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """
        处理级联结果，统一处理"-"逻辑

        Args:
            options: 原始选项列表
            request_id_field: 请求中对应的ID字段值

        Returns:
            (处理后的选项列表, 空值ID)
        """
        # 如果只有一个元素，并且name是"-"，则返回空列表，并提供空值ID供下级使用
        null_id = None
        if len(options) == 1 and options[0]["name"] == "-":
            null_id = options[0]["id"]
            options = []

        return options, null_id
