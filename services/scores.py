from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, and_, func
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.exc import IntegrityError

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
        获取评分列表数据

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
            raise Exception(f"获取评分列表失败: {str(e)}")

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
            bridge_instance_options = self._get_bridge_instance_options()

            assessment_unit_instance_options = (
                self._get_assessment_unit_instance_options(bridge_instance_name)
            )

            bridge_type_options = self._get_bridge_type_options_for_scores(
                bridge_instance_name, assessment_unit_instance_name
            )

            return {
                "bridge_instance_options": bridge_instance_options,
                "assessment_unit_instance_options": assessment_unit_instance_options,
                "bridge_type_options": bridge_type_options,
            }

        except Exception as e:
            print(f"获取级联选项时出错: {e}")
            raise Exception(f"获取级联选项失败: {str(e)}")

    def _get_bridge_instance_options(self) -> List[Dict[str, Any]]:
        """获取桥梁实例名称选项"""
        try:
            stmt = (
                select(UserPaths.bridge_instance_name)
                .where(and_(UserPaths.is_active == True))
                .distinct()
                .order_by(UserPaths.bridge_instance_name)
            )

            results = self.session.exec(stmt).all()
            return [{"name": name} for name in results if name]

        except Exception as e:
            print(f"获取桥梁实例名称选项时出错: {e}")
            return []

    def _get_assessment_unit_instance_options(
        self, bridge_instance_name: Optional[str]
    ) -> List[Dict[str, Any]]:
        """获取评定单元实例名称选项"""
        try:
            conditions = [UserPaths.is_active == True]

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

    def calculate_score(self, request: ScoreListRequest) -> Dict[str, Any]:
        """
        计算评分
        """
        try:
            # 获取用户在该链路构件下录入的病害数据
            pass

        except Exception as e:
            raise Exception(f"计算评分失败: {str(e)}")


def get_scores_service(session: Session) -> ScoresService:
    """获取评分服务实例"""
    return ScoresService(session)
