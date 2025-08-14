from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, and_, func
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.exc import IntegrityError
import math

from models import (
    WeightReferences,
    Paths,
    BridgeParts,
    BridgeStructures,
    BridgeComponentTypes,
    BridgeComponentForms,
    BridgeTypes,
    Scores,
    UserPaths,
    BridgePartWeight,
    InspectionRecords,
    BridgeScales,
    AssessmentUnit,
)
from schemas.scores import (
    ScoreListRequest,
    ScoreItemData,
    ScoreListPageResponse,
    ScoresCascadeOptionsResponse,
    CalculationMode,
    WeightAllocationRequest,
    WeightAllocationSaveRequest,
)
from services.base_crud import PageParams
from services.component_deduction import ComponentDeductionService
from exceptions import NotFoundException


class ScoresService:
    """评分服务类"""

    def __init__(self, session: Session):
        self.session = session

    def _get_saved_scores_data(
        self, request: ScoreListRequest
    ) -> Optional[Dict[Tuple[int, int], Dict[str, Any]]]:
        """
        获取scores表中保存的数据

        Args:
            request: 查询请求参数

        Returns:
            保存的scores数据字典 {(part_id, component_type_id): {数据}}，如果没有数据返回None
        """
        try:
            conditions = [
                Scores.bridge_instance_name == request.bridge_instance_name,
                Scores.bridge_type_id == request.bridge_type_id,
                Scores.is_active == True,
            ]

            if request.assessment_unit_instance_name:
                conditions.append(
                    Scores.assessment_unit_instance_name
                    == request.assessment_unit_instance_name
                )
            else:
                conditions.append(Scores.assessment_unit_instance_name.is_(None))

            if request.user_id:
                conditions.append(Scores.user_id == request.user_id)
            else:
                conditions.append(Scores.user_id.is_(None))

            stmt = select(
                Scores.part_id,
                Scores.component_type_id,
                Scores.component_count,
                Scores.custom_component_count,
                Scores.adjusted_weight,
            ).where(and_(*conditions))

            results = self.session.exec(stmt).all()

            if not results:
                return None

            saved_data = {}
            for row in results:
                key = (row.part_id, row.component_type_id)
                saved_data[key] = {
                    "component_count": row.component_count,
                    "custom_component_count": row.custom_component_count
                    or row.component_count,
                    "adjusted_weight": row.adjusted_weight or Decimal("0"),
                }

            return saved_data

        except Exception as e:
            print(f"查询scores表保存数据失败: {e}")
            return None

    def get_score_list(
        self, request: ScoreListRequest
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取权重分配列表数据

        Args:
            request: 查询请求参数

        Returns:
            评分数据字典列表和总数的元组
        """
        try:
            weight_data = self._get_weight_data(request)

            if not weight_data:
                return [], 0

            saved_scores_data = self._get_saved_scores_data(request)

            score_data = []
            for item in weight_data:
                key = (item["part_id"], item["component_type_id"])

                if saved_scores_data and key in saved_scores_data:
                    saved_item = saved_scores_data[key]
                    component_count = saved_item["component_count"]
                    custom_count = saved_item["custom_component_count"]
                    adjusted_weight = saved_item["adjusted_weight"]
                else:
                    component_count = self._count_components_from_paths(request, item)
                    custom_count = component_count
                    adjusted_weight = self._calculate_adjusted_weight(
                        item["weight"], custom_count
                    )

                score_item = {
                    "part_id": item["part_id"],
                    "part_name": item["part_name"],
                    "component_type_id": item["component_type_id"],
                    "component_type_name": item["component_type_name"],
                    "weight": float(item["weight"]),
                    "component_count": component_count,
                    "custom_component_count": custom_count,
                    "adjusted_weight": float(adjusted_weight),
                }
                score_data.append(score_item)

            return score_data, len(score_data)

        except Exception as e:
            raise Exception(f"获取权重分配列表失败: {str(e)}")

    def _get_weight_data(self, request: ScoreListRequest) -> List[Dict[str, Any]]:
        """
        获取权重数据
        从weight_references表查询权重，按bridge_type_id到component_type_id链路
        """
        try:
            conditions = [
                WeightReferences.bridge_type_id == request.bridge_type_id,
                WeightReferences.is_active == True,
            ]

            stmt = (
                select(
                    WeightReferences.part_id,
                    WeightReferences.structure_id,
                    WeightReferences.component_type_id,
                    WeightReferences.weight,
                    BridgeParts.name.label("part_name"),
                    BridgeComponentTypes.name.label("component_type_name"),
                )
                .join(BridgeParts, WeightReferences.part_id == BridgeParts.id)
                .join(
                    BridgeComponentTypes,
                    WeightReferences.component_type_id == BridgeComponentTypes.id,
                )
                .where(and_(*conditions))
                .order_by(
                    WeightReferences.part_id,
                    WeightReferences.component_type_id,
                )
            )

            results = self.session.exec(stmt).all()

            weight_data = []
            for row in results:
                weight_data.append(
                    {
                        "part_id": row.part_id,
                        "part_name": row.part_name,
                        "structure_id": row.structure_id,
                        "component_type_id": row.component_type_id,
                        "component_type_name": row.component_type_name,
                        "weight": row.weight,
                    }
                )

            return weight_data

        except Exception as e:
            print(f"查询权重数据失败: {e}")
            return []

    def _count_components_from_paths(
        self, request: ScoreListRequest, weight_item: Dict[str, Any]
    ) -> int:
        """
        统计构件数量
        统计paths表中对应权重链路的记录数量，排除构件形式为"-"的记录
        """
        try:
            conditions = [
                Paths.bridge_type_id == request.bridge_type_id,
                Paths.part_id == weight_item["part_id"],
                Paths.component_type_id == weight_item["component_type_id"],
                Paths.is_active == True,
                Paths.component_form_id.is_not(None),  # 排除空值
            ]

            # 结构类型过滤
            if weight_item.get("structure_id"):
                conditions.append(Paths.structure_id == weight_item["structure_id"])

            # 统计符合条件的paths记录数量，排除构件形式为"-"的记录
            stmt = (
                select(func.count(func.distinct(Paths.component_form_id)))
                .join(
                    BridgeComponentForms,
                    Paths.component_form_id == BridgeComponentForms.id,
                )
                .where(
                    and_(
                        *conditions,
                        BridgeComponentForms.name != "-",  # 排除构件形式为"-"的记录
                        BridgeComponentForms.is_active == True,
                    )
                )
            )

            count = self.session.exec(stmt).first() or 0
            return count

        except Exception as e:
            print(f"统计构件数量失败: {e}")
            return 0

    def _calculate_adjusted_weight(
        self, weight: Decimal, component_count: int
    ) -> Decimal:
        """
        计算调整后权重
        目前暂时设为 0，后续会实现具体的计算逻辑
        """
        try:
            # 暂时返回 0，后续实现计算逻辑
            return Decimal("0.0000")

        except Exception as e:
            print(f"计算调整后权重失败: {e}")
            return Decimal("0.0000")

    def get_cascade_options(
        self,
        bridge_instance_name: Optional[str] = None,
        assessment_unit_instance_name: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        获取权重分配分页查询的级联下拉选项

        Args:
            bridge_instance_name: 桥梁实例名称（可选）
            assessment_unit_instance_name: 评定单元实例名称（可选）

        Returns:
            级联选项字典
        """
        try:
            bridge_instance_options = self._get_bridge_instance_options(user_id)

            assessment_unit_instance_options = (
                self._get_assessment_unit_instance_options(
                    bridge_instance_name, user_id
                )
            )

            bridge_type_options = self._get_bridge_type_options_for_scores(
                bridge_instance_name, assessment_unit_instance_name, user_id
            )

            return {
                "bridge_instance_options": bridge_instance_options,
                "assessment_unit_instance_options": assessment_unit_instance_options,
                "bridge_type_options": bridge_type_options,
            }

        except Exception as e:
            print(f"获取级联选项时出错: {e}")
            raise Exception(f"获取级联选项失败: {str(e)}")

    def _get_bridge_instance_options(
        self, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取桥梁实例名称选项"""
        try:
            conditions = [UserPaths.is_active == True]
            if user_id is not None:
                conditions.append(UserPaths.user_id == user_id)
            else:
                conditions.append(UserPaths.user_id.is_(None))

            stmt = (
                select(UserPaths.bridge_instance_name)
                .where(and_(*conditions))
                .distinct()
                .order_by(UserPaths.bridge_instance_name)
            )

            results = self.session.exec(stmt).all()
            return [{"name": name} for name in results if name]

        except Exception as e:
            print(f"获取桥梁实例名称选项时出错: {e}")
            return []

    def _get_assessment_unit_instance_options(
        self, bridge_instance_name: Optional[str], user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取评定单元实例名称选项"""
        try:
            conditions = [UserPaths.is_active == True]

            if user_id is not None:
                conditions.append(UserPaths.user_id == user_id)
            else:
                conditions.append(UserPaths.user_id.is_(None))

            if bridge_instance_name:
                conditions.append(
                    UserPaths.bridge_instance_name == bridge_instance_name
                )
            else:
                conditions.append(UserPaths.assessment_unit_instance_name.is_(None))

            stmt = (
                select(UserPaths.assessment_unit_instance_name)
                .where(and_(*conditions))
                .distinct()
                .order_by(UserPaths.assessment_unit_instance_name)
            )

            results = self.session.exec(stmt).all()
            return [{"name": name} for name in results if name is not None]

        except Exception as e:
            print(f"获取评定单元实例名称选项时出错: {e}")
            return []

    def _get_bridge_type_options_for_scores(
        self,
        bridge_instance_name: Optional[str],
        assessment_unit_instance_name: Optional[str],
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """获取桥梁类型选项"""
        try:
            conditions = [UserPaths.is_active == True]

            if bridge_instance_name:
                conditions.append(
                    UserPaths.bridge_instance_name == bridge_instance_name
                )
            else:
                conditions.append(UserPaths.bridge_type_id.is_(None))

            if user_id is not None:
                conditions.append(UserPaths.user_id == user_id)
            else:
                conditions.append(UserPaths.user_id.is_(None))

            if assessment_unit_instance_name:
                conditions.append(
                    UserPaths.assessment_unit_instance_name
                    == assessment_unit_instance_name
                )
            else:
                conditions.append(UserPaths.assessment_unit_id.is_(None))

            # 查询桥梁类型ID并关联桥梁类型表获取名称
            stmt = (
                select(UserPaths.bridge_type_id, BridgeTypes.name)
                .join(BridgeTypes, UserPaths.bridge_type_id == BridgeTypes.id)
                .where(
                    and_(
                        *conditions,
                        BridgeTypes.is_active == True,
                    )
                )
                .distinct()
                .order_by(BridgeTypes.name)
            )

            results = self.session.exec(stmt).all()
            return [{"id": r[0], "name": r[1]} for r in results]

        except Exception as e:
            print(f"获取桥梁类型选项时出错: {e}")
            return []

    def _prepare_component_counts(
        self,
        score_request: ScoreListRequest,
        weight_data: List[Dict[str, Any]],
        allocation_request: WeightAllocationRequest,
    ) -> Dict[Tuple[int, int], int]:
        """
        构件数量数据

        Args:
            score_request: 评分查询请求
            weight_data: 权重数据
            allocation_request: 权重分配请求

        Returns:
            构件数量字典 {(part_id, component_type_id): count}
        """
        component_counts = {}

        if allocation_request.calculation_mode == CalculationMode.DEFAULT:
            for item in weight_data:
                key = (item["part_id"], item["component_type_id"])
                count = self._count_components_from_paths(score_request, item)
                component_counts[key] = count
        else:
            custom_counts = {
                (item.part_id, item.component_type_id): item.custom_component_count
                for item in allocation_request.custom_component_counts
            }

            for item in weight_data:
                key = (item["part_id"], item["component_type_id"])
                # 优先使用自定义数量，否则使用默认数量
                if key in custom_counts:
                    component_counts[key] = custom_counts[key]
                else:
                    count = self._count_components_from_paths(score_request, item)
                    component_counts[key] = count

        return component_counts

    def _allocate_weights_for_part(
        self, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        对单个部位的部件应用权重分配规则

        Args:
            items: 同一部位的部件列表

        Returns:
            应用权重分配规则后的部件列表
        """
        zero_count_items = [item for item in items if item["used_component_count"] == 0]
        non_zero_count_items = [
            item for item in items if item["used_component_count"] > 0
        ]

        # 所有构件数量都不为0，无需分配
        if not zero_count_items:
            return items

        # 所有构件数量都为0，调整后权重都为0
        if not non_zero_count_items:
            for item in items:
                item["adjusted_weight"] = Decimal("0")
            return items

        # 计算需要分配的权重总和（构件数量为0的部件权重之和）
        zero_weight_sum = sum(item["original_weight"] for item in zero_count_items)

        # 计算非0部件的原始权重总和
        non_zero_weight_sum = sum(
            item["original_weight"] for item in non_zero_count_items
        )

        # 对构件数量为0的部件，调整后权重设为0
        for item in zero_count_items:
            item["adjusted_weight"] = Decimal("0")

        # 对构件数量非0的部件，重新计算权重
        for item in non_zero_count_items:
            current_weight = item["original_weight"]
            if non_zero_weight_sum > 0:
                # ((当前部件权重 / 非0部件权重总和) * 0部件权重总和) + 当前部件权重
                allocation_factor = current_weight / non_zero_weight_sum
                allocated_weight = allocation_factor * zero_weight_sum
                item["adjusted_weight"] = current_weight + allocated_weight
            else:
                item["adjusted_weight"] = current_weight

        return items

    def _apply_weight_allocation_rules(
        self,
        weight_data: List[Dict[str, Any]],
        component_counts: Dict[Tuple[int, int], int],
    ) -> List[Dict[str, Any]]:
        """
        应用权重分配规则

        Args:
            weight_data: 权重数据
            component_counts: 构件数量数据

        Returns:
            应用权重分配规则后的数据列表
        """
        # 按部位分组
        parts_data = defaultdict(list)
        for item in weight_data:
            key = (item["part_id"], item["component_type_id"])
            default_count = component_counts.get(key, 0)

            enhanced_item = {
                **item,
                "default_component_count": default_count,
                "used_component_count": default_count,
                "original_weight": item["weight"],
                "adjusted_weight": item["weight"],
            }
            parts_data[item["part_id"]].append(enhanced_item)

        # 对每个部位应用权重分配规则
        result_data = []
        for part_id, items in parts_data.items():
            allocated_items = self._allocate_weights_for_part(items)
            result_data.extend(allocated_items)

        return result_data

    def calculate_weight_allocation(
        self, request: WeightAllocationRequest
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        权重分配计算

        Args:
            request: 权重分配计算请求参数

        Returns:
            权重分配结果（数据字典列表和总数）
        """
        try:
            score_request = ScoreListRequest(
                bridge_instance_name=request.bridge_instance_name,
                bridge_type_id=request.bridge_type_id,
                assessment_unit_instance_name=request.assessment_unit_instance_name,
            )

            weight_data = self._get_weight_data(score_request)
            if not weight_data:
                return [], 0

            component_counts = self._prepare_component_counts(
                score_request, weight_data, request
            )

            # 按部位分组
            allocated_data = self._apply_weight_allocation_rules(
                weight_data, component_counts
            )

            result_data = []
            for item in allocated_data:
                score_item = {
                    "part_id": item["part_id"],
                    "part_name": item["part_name"],
                    "component_type_id": item["component_type_id"],
                    "component_type_name": item["component_type_name"],
                    "weight": float(item["original_weight"]),
                    "component_count": item["default_component_count"],
                    "custom_component_count": item["used_component_count"],
                    "adjusted_weight": float(item["adjusted_weight"]),
                }
                result_data.append(score_item)

            return result_data, len(result_data)

        except Exception as e:
            raise Exception(f"权重分配计算失败: {str(e)}")

    def _is_first_save(self, request: WeightAllocationSaveRequest) -> bool:
        """
        检查是否为第一次保存

        Args:
            request: 保存请求参数

        Returns:
            是否为第一次保存
        """
        conditions = [
            Scores.bridge_instance_name == request.bridge_instance_name,
            Scores.bridge_type_id == request.bridge_type_id,
            Scores.is_active == True,
        ]

        if request.assessment_unit_instance_name:
            conditions.append(
                Scores.assessment_unit_instance_name
                == request.assessment_unit_instance_name
            )
        else:
            conditions.append(Scores.assessment_unit_instance_name.is_(None))

        stmt = select(func.count(Scores.id)).where(and_(*conditions))
        count = self.session.exec(stmt).one()

        return count == 0

    def _get_structure_ids(
        self, request: WeightAllocationSaveRequest
    ) -> Dict[Tuple[int, int], Optional[int]]:
        """
        获取structure_id映射

        Args:
            request: 保存请求参数

        Returns:
            structure_id映射字典 {(part_id, component_type_id): structure_id}
        """
        # 从weight_references表获取structure_id
        stmt = select(
            WeightReferences.part_id,
            WeightReferences.component_type_id,
            WeightReferences.structure_id,
        ).where(
            and_(
                WeightReferences.bridge_type_id == request.bridge_type_id,
                WeightReferences.is_active == True,
            )
        )

        results = self.session.exec(stmt).all()
        structure_id_map = {}

        for row in results:
            key = (row.part_id, row.component_type_id)
            structure_id_map[key] = row.structure_id

        return structure_id_map

    def _batch_insert_scores(
        self,
        request: WeightAllocationSaveRequest,
        structure_id_map: Dict[Tuple[int, int], Optional[int]],
    ) -> None:
        """
        批量插入scores记录

        Args:
            request: 保存请求参数
            structure_id_map: structure_id映射
        """
        use_custom_count = request.calculation_mode == CalculationMode.CUSTOM

        scores_list = []
        for item in request.items:
            key = (item.part_id, item.component_type_id)
            structure_id = structure_id_map.get(key)

            score_record = Scores(
                bridge_instance_name=request.bridge_instance_name,
                assessment_unit_instance_name=request.assessment_unit_instance_name,
                bridge_type_id=request.bridge_type_id,
                part_id=item.part_id,
                structure_id=structure_id,
                component_type_id=item.component_type_id,
                weight=item.weight,
                component_count=item.component_count,
                custom_component_count=item.custom_component_count,
                adjusted_weight=item.adjusted_weight,
                use_custom_count=use_custom_count,
                is_active=True,
            )
            scores_list.append(score_record)

        # 批量插入
        self.session.add_all(scores_list)

    def _batch_update_scores(self, request: WeightAllocationSaveRequest) -> None:
        """
        批量更新scores记录

        Args:
            request: 保存请求参数
        """
        use_custom_count = request.calculation_mode == CalculationMode.CUSTOM

        base_conditions = [
            Scores.bridge_instance_name == request.bridge_instance_name,
            Scores.bridge_type_id == request.bridge_type_id,
            Scores.is_active == True,
        ]

        if request.assessment_unit_instance_name:
            base_conditions.append(
                Scores.assessment_unit_instance_name
                == request.assessment_unit_instance_name
            )
        else:
            base_conditions.append(Scores.assessment_unit_instance_name.is_(None))

        # 更新
        for item in request.items:
            conditions = base_conditions + [
                Scores.part_id == item.part_id,
                Scores.component_type_id == item.component_type_id,
            ]

            update_data = {
                "adjusted_weight": item.adjusted_weight,
                "use_custom_count": use_custom_count,
            }

            # 自定义构件计算，更新自定义构件数量
            if use_custom_count:
                update_data["custom_component_count"] = item.custom_component_count

            stmt = (
                Scores.__table__.update().where(and_(*conditions)).values(**update_data)
            )

            self.session.execute(stmt)

    def save_weight_allocation(self, request: WeightAllocationSaveRequest) -> bool:
        """
        保存权重分配数据

        Args:
            request: 权重分配保存请求参数

        Returns:
            保存是否成功
        """
        try:
            # 检查是否为第一次保存
            is_first_save = self._is_first_save(request)

            # 获取structure_id映射
            structure_id_map = self._get_structure_ids(request)

            if is_first_save:
                # 第一次保存批量插入所有记录
                self._batch_insert_scores(request, structure_id_map)
            else:
                # 批量更新记录
                self._batch_update_scores(request)

            self.session.commit()
            return True

        except IntegrityError as e:
            self.session.rollback()
            raise Exception(f"数据完整性错误: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"保存权重分配数据失败: {str(e)}")

    def get_score_table_data(self, request: ScoreListRequest) -> Dict[str, Any]:
        """
        获取评分表格数据

        Args:
            request: 查询请求参数

        Returns:
            评分表格数据
        """
        try:
            weight_data = self._get_weight_data(request)
            if not weight_data:
                return {"总体评分": 0.00, "评定等级": "暂无", "部位": {}}

            saved_scores_data = self._get_saved_scores_data(request)

            # 按部位分组数据
            parts_data = defaultdict(
                lambda: {"部位权重": 0.00, "部位评分": 0.00, "部件": {}}
            )

            # 处理每个部件数据
            for item in weight_data:
                part_name = item["part_name"]
                component_type_name = item["component_type_name"]
                key = (item["part_id"], item["component_type_id"])

                # 获取调整后权重
                if saved_scores_data and key in saved_scores_data:
                    adjusted_weight = saved_scores_data[key]["adjusted_weight"]
                else:
                    component_count = self._count_components_from_paths(request, item)
                    custom_count = component_count
                    adjusted_weight = self._calculate_adjusted_weight(
                        item["weight"], custom_count
                    )

                # 部件数据
                parts_data[part_name]["部件"][component_type_name] = {
                    "权重": float(adjusted_weight),
                    "部件评分": 0.00,
                }

            # 计算部位权重
            for part_name, part_info in parts_data.items():
                # 获取部位权重
                part_weight = BridgePartWeight.get_weight_by_name(part_name)
                if part_weight is not None:
                    parts_data[part_name]["部位权重"] = part_weight
                else:
                    parts_data[part_name]["部位权重"] = 0.00

            result = {
                "总体评分": 0.00,
                "评定等级": "暂无",
                "部位": dict(parts_data),
            }

            return result

        except Exception as e:
            raise Exception(f"获取评分表格数据失败: {str(e)}")

    def _get_user_damage_records(
        self, request: ScoreListRequest
    ) -> List[Dict[str, Any]]:
        """
        获取用户在该链路构件下录入的病害数据，按构件分组

        Args:
            request: 评分列表查询请求

        Returns:
            按构件分组的病害数据列表
        """
        try:
            user_path_conditions = [
                UserPaths.bridge_instance_name == request.bridge_instance_name,
                UserPaths.bridge_type_id == request.bridge_type_id,
                UserPaths.is_active == True,
            ]

            if request.assessment_unit_instance_name:
                user_path_conditions.append(
                    UserPaths.assessment_unit_instance_name
                    == request.assessment_unit_instance_name
                )
            else:
                user_path_conditions.append(
                    UserPaths.assessment_unit_instance_name.is_(None)
                )

            if request.user_id is not None:
                user_path_conditions.append(UserPaths.user_id == request.user_id)
            else:
                user_path_conditions.append(UserPaths.user_id.is_(None))

            user_paths_stmt = select(UserPaths).where(and_(*user_path_conditions))
            user_paths = self.session.exec(user_paths_stmt).all()

            if not user_paths:
                return []

            # 查找病害记录
            damage_records = []

            for user_path in user_paths:
                damage_conditions = [
                    InspectionRecords.bridge_instance_name
                    == user_path.bridge_instance_name,
                    InspectionRecords.bridge_type_id == user_path.bridge_type_id,
                    InspectionRecords.part_id == user_path.part_id,
                    InspectionRecords.is_active == True,
                ]

                if user_path.assessment_unit_instance_name:
                    damage_conditions.append(
                        InspectionRecords.assessment_unit_instance_name
                        == user_path.assessment_unit_instance_name
                    )
                else:
                    damage_conditions.append(
                        InspectionRecords.assessment_unit_instance_name.is_(None)
                    )

                if user_path.structure_id:
                    damage_conditions.append(
                        InspectionRecords.structure_id == user_path.structure_id
                    )
                else:
                    damage_conditions.append(InspectionRecords.structure_id.is_(None))

                if user_path.component_type_id:
                    damage_conditions.append(
                        InspectionRecords.component_type_id
                        == user_path.component_type_id
                    )
                else:
                    damage_conditions.append(
                        InspectionRecords.component_type_id.is_(None)
                    )

                if user_path.component_form_id:
                    damage_conditions.append(
                        InspectionRecords.component_form_id
                        == user_path.component_form_id
                    )
                else:
                    damage_conditions.append(
                        InspectionRecords.component_form_id.is_(None)
                    )

                if request.user_id is not None:
                    damage_conditions.append(
                        InspectionRecords.user_id == request.user_id
                    )
                else:
                    damage_conditions.append(InspectionRecords.user_id.is_(None))

                damage_stmt = select(InspectionRecords).where(and_(*damage_conditions))
                records = self.session.exec(damage_stmt).all()

                # 为每条记录添加构件信息
                for record in records:
                    damage_info = {
                        "record_id": record.id,
                        "bridge_instance_name": record.bridge_instance_name,
                        "assessment_unit_instance_name": record.assessment_unit_instance_name,
                        "bridge_type_id": record.bridge_type_id,
                        "part_id": record.part_id,
                        "structure_id": record.structure_id,
                        "component_type_id": record.component_type_id,
                        "component_form_id": record.component_form_id,
                        "component_name": record.component_name,
                        "damage_type_id": record.damage_type_id,
                        "scale_id": record.scale_id,
                        "damage_location": record.damage_location,
                        "damage_description": record.damage_description,
                        "image_url": record.image_url,
                        "created_at": record.created_at,
                        # 构件标识（用于分组）
                        "component_key": f"{record.part_id}_{record.component_type_id}_{record.component_form_id}_{record.component_name or 'default'}",
                    }
                    damage_records.append(damage_info)

            return damage_records

        except Exception as e:
            raise Exception(f"获取用户病害数据失败: {str(e)}")

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

    def _get_max_scale_for_damage_type(
        self, damage_type_id: int, record: Dict[str, Any]
    ) -> Optional[int]:
        """
        获取指定病害类型在特定路径下的最高标度值

        Args:
            damage_type_id: 病害类型ID
            record: 病害记录（包含路径信息）

        Returns:
            最高标度值
        """
        try:
            # 获取用户路径信息
            user_path_conditions = [
                UserPaths.bridge_instance_name == record["bridge_instance_name"],
                UserPaths.bridge_type_id == record["bridge_type_id"],
                UserPaths.part_id == record["part_id"],
                UserPaths.is_active == True,
            ]

            if record.get("assessment_unit_instance_name"):
                user_path_conditions.append(
                    UserPaths.assessment_unit_instance_name
                    == record["assessment_unit_instance_name"]
                )
            else:
                user_path_conditions.append(
                    UserPaths.assessment_unit_instance_name.is_(None)
                )

            if record.get("structure_id"):
                user_path_conditions.append(
                    UserPaths.structure_id == record["structure_id"]
                )
            else:
                user_path_conditions.append(UserPaths.structure_id.is_(None))

            if record.get("component_type_id"):
                user_path_conditions.append(
                    UserPaths.component_type_id == record["component_type_id"]
                )
            else:
                user_path_conditions.append(UserPaths.component_type_id.is_(None))

            if record.get("component_form_id"):
                user_path_conditions.append(
                    UserPaths.component_form_id == record["component_form_id"]
                )
            else:
                user_path_conditions.append(UserPaths.component_form_id.is_(None))

            # 查询用户路径记录
            user_path_stmt = select(UserPaths).where(and_(*user_path_conditions))
            user_path = self.session.exec(user_path_stmt).first()

            if not user_path:
                return None

            # 通过用户路径的 paths_id 获取基础路径信息
            paths_stmt = select(Paths).where(
                and_(Paths.id == user_path.paths_id, Paths.is_active == True)
            )
            paths_record = self.session.exec(paths_stmt).first()

            if not paths_record:
                return None

            conditions = [
                Paths.category_id == paths_record.category_id,
                Paths.bridge_type_id == paths_record.bridge_type_id,
                Paths.part_id == paths_record.part_id,
                Paths.disease_id == damage_type_id,
                Paths.scale_id.is_not(None),
                Paths.is_active == True,
            ]

            if paths_record.assessment_unit_id is not None:
                conditions.append(
                    Paths.assessment_unit_id == paths_record.assessment_unit_id
                )
            else:
                conditions.append(Paths.assessment_unit_id.is_(None))

            if paths_record.structure_id is not None:
                conditions.append(Paths.structure_id == paths_record.structure_id)
            else:
                conditions.append(Paths.structure_id.is_(None))

            if paths_record.component_type_id is not None:
                conditions.append(
                    Paths.component_type_id == paths_record.component_type_id
                )
            else:
                conditions.append(Paths.component_type_id.is_(None))

            if paths_record.component_form_id is not None:
                conditions.append(
                    Paths.component_form_id == paths_record.component_form_id
                )
            else:
                conditions.append(Paths.component_form_id.is_(None))

            # 查询该病害类型下的所有标度值
            scales_stmt = (
                select(BridgeScales.scale_value)
                .join(Paths, Paths.scale_id == BridgeScales.id)
                .where(and_(*conditions, BridgeScales.is_active == True))
                .distinct()
            )

            scale_values = self.session.exec(scales_stmt).all()

            if scale_values:
                return max(scale_values)

            return None

        except Exception as e:
            print(f"获取最高标度失败: {e}")
            return None

    def _get_scale_value(self, scale_id: int) -> Optional[int]:
        """
        获取标度值

        Args:
            scale_id: 标度ID

        Returns:
            标度值
        """
        try:
            stmt = select(BridgeScales.scale_value).where(
                and_(BridgeScales.id == scale_id, BridgeScales.is_active == True)
            )
            return self.session.exec(stmt).first()

        except Exception as e:
            print(f"获取标度值失败: {e}")
            return None

    def _calculate_damage_scores(
        self, damage_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        计算病害分数

        Args:
            damage_records: 病害记录列表

        Returns:
            包含分数的病害记录列表
        """
        try:
            damage_scores = []

            for record in damage_records:
                damage_type_id = record["damage_type_id"]
                scale_id = record["scale_id"]

                # 获取该病害类型的最高标度
                max_scale = self._get_max_scale_for_damage_type(damage_type_id, record)

                # 获取当前标度值
                current_scale_value = self._get_scale_value(scale_id)

                # 计算病害分数
                damage_score = 0
                if max_scale and current_scale_value:
                    damage_score = (
                        ComponentDeductionService.get_deduction_value(
                            max_scale, current_scale_value
                        )
                        or 0
                    )

                # 添加分数信息到记录中
                score_record = record.copy()
                score_record.update(
                    {
                        "max_scale": max_scale,
                        "current_scale_value": current_scale_value,
                        "damage_score": damage_score,
                    }
                )

                damage_scores.append(score_record)

            return damage_scores

        except Exception as e:
            raise Exception(f"计算病害分数失败: {str(e)}")

    def _calculate_single_component_score(self, damages: List[Dict[str, Any]]) -> float:
        """
        计算单个构件的分数

        Args:
            damages: 该构件的所有病害记录

        Returns:
            构件分数
        """
        try:
            damage_count = len(damages)

            # 病害数量 = 0，构件分数 = 100
            if damage_count == 0:
                return 100.0

            # 病害数量 = 1，构件分数 = 100 - 病害分数
            if damage_count == 1:
                return 100.0 - damages[0]["damage_score"]

            # 病害数量 >= 100，构件分数 = 0
            if damage_count >= 100:
                return 0.0

            # 病害数量 >= 2
            # 病害分数降序排序
            damage_scores = [d["damage_score"] for d in damages]
            damage_scores.sort(reverse=True)

            # 累计计算U值
            total_u = 0.0

            for i, score in enumerate(damage_scores, 1):
                # U_i = (score / (100 * √i)) * (100 - total_u)
                u_i = (score / (100 * math.sqrt(i))) * (100 - total_u)
                total_u += u_i

            # 构件分数 = 100 - total_u
            component_score = 100.0 - total_u

            return max(0.0, component_score)

        except Exception as e:
            print(f"计算单个构件分数失败: {e}")
            return 0.0

    def _get_all_components_from_paths(
        self, request: ScoreListRequest
    ) -> Dict[str, Dict[str, Any]]:
        """
        从paths表获取该桥梁类型下的所有构件信息

        Args:
            request: 评分请求参数

        Returns:
            构件信息字典 {component_key: component_info}
        """
        try:
            # 查询该桥梁类型下的所有构件路径
            conditions = [
                Paths.bridge_type_id == request.bridge_type_id,
                Paths.part_id.is_not(None),
                Paths.is_active == True,
            ]

            # 获取名称信息
            stmt = (
                select(
                    Paths.part_id,
                    Paths.structure_id,
                    Paths.component_type_id,
                    Paths.component_form_id,
                    BridgeParts.name.label("part_name"),
                    BridgeStructures.name.label("structure_name"),
                    BridgeComponentTypes.name.label("component_type_name"),
                    BridgeComponentForms.name.label("component_form_name"),
                )
                .select_from(Paths)
                .join(BridgeParts, Paths.part_id == BridgeParts.id, isouter=False)
                .join(
                    BridgeStructures,
                    Paths.structure_id == BridgeStructures.id,
                    isouter=True,
                )
                .join(
                    BridgeComponentTypes,
                    Paths.component_type_id == BridgeComponentTypes.id,
                    isouter=True,
                )
                .join(
                    BridgeComponentForms,
                    Paths.component_form_id == BridgeComponentForms.id,
                    isouter=True,
                )
                .where(and_(*conditions))
                .distinct()
            )

            records = self.session.exec(stmt).all()

            components = {}

            for record in records:
                # 构件的唯一标识：部位+部件类型+构件形式
                component_key = f"{record.part_id}_{record.component_type_id or 'null'}_{record.component_form_id or 'null'}"

                # 避免重复
                if component_key not in components:
                    component_info = {
                        "bridge_instance_name": request.bridge_instance_name,
                        "assessment_unit_instance_name": request.assessment_unit_instance_name,
                        "bridge_type_id": request.bridge_type_id,
                        "part_id": record.part_id,
                        "part_name": record.part_name,
                        "structure_id": record.structure_id,
                        "structure_name": record.structure_name,
                        "component_type_id": record.component_type_id,
                        "component_type_name": record.component_type_name,
                        "component_form_id": record.component_form_id,
                        "component_form_name": record.component_form_name,
                    }

                    components[component_key] = component_info

            print(f"从paths表获取到 {len(components)} 个构件:")
            for key, info in components.items():
                print(
                    f"  - {key}: {info['part_name']}/{info['component_type_name'] or 'None'}/{info['component_form_name'] or 'None'}"
                )

            return components

        except Exception as e:
            print(f"从paths表获取构件信息失败: {e}")
            return {}

    def _calculate_component_scores(
        self, damage_scores: List[Dict[str, Any]], request: ScoreListRequest
    ) -> Dict[str, Dict[str, Any]]:
        """
        按构件分组并计算构件分数

        Args:
            damage_scores: 包含分数的病害记录列表
            request: 评分请求参数

        Returns:
            构件分数字典 {component_key: {component_info, damages, component_score}}
        """
        try:
            # 获取桥梁类型下的所有构件信息
            all_components = self._get_all_components_from_paths(request)

            # 按构件分组病害数据
            components_with_damages = defaultdict(list)

            for damage in damage_scores:
                component_key = damage["component_key"]
                components_with_damages[component_key].append(damage)

            component_scores = {}

            print(f"开始计算构件分数，共 {len(all_components)} 个构件:")

            # 计算每个构件的分数
            for component_key, component_info in all_components.items():
                damages = components_with_damages.get(component_key, [])

                # 计算构件分数
                component_score = self._calculate_single_component_score(damages)

                component_name = f"{component_info['part_name']}/{component_info['component_type_name'] or 'None'}/{component_info['component_form_name'] or 'None'}"
                damage_count = len(damages)

                print(
                    f"  - {component_name}: {damage_count}个病害, 分数={component_score:.2f}"
                )

                component_scores[component_key] = {
                    "component_info": component_info,
                    "damages": damages,
                    "damage_count": len(damages),
                    "component_score": component_score,
                }

            return component_scores

        except Exception as e:
            raise Exception(f"计算构件分数失败: {str(e)}")

    def calculate_score(self, request: ScoreListRequest) -> Dict[str, Any]:
        """
        计算评分
        """
        try:
            # 获取用户在该链路构件下录入的病害数据
            damage_records = self._get_user_damage_records(request)

            # 计算病害分数
            damage_scores = self._calculate_damage_scores(damage_records)

            # 计算构件分数
            component_scores = self._calculate_component_scores(damage_scores, request)

            return {
                "damage_records": damage_records,
                "damage_scores": damage_scores,
                "component_scores": component_scores,
                "message": "评分计算成功",
            }

        except Exception as e:
            raise Exception(f"计算评分失败: {str(e)}")


def get_scores_service(session: Session) -> ScoresService:
    """获取评分服务实例"""
    return ScoresService(session)
