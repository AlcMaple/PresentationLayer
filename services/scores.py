from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, and_, func
from decimal import Decimal

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
)
from schemas.scores import (
    ScoreListRequest,
    ScoreItemData,
    ScoreListPageResponse,
    ScoresCascadeOptionsResponse,
)
from services.base_crud import PageParams
from exceptions import NotFoundException


class ScoresService:
    """评分服务类"""

    def __init__(self, session: Session):
        self.session = session

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

            score_data = []
            for item in weight_data:
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
            # 暂时返回 0，等待后续实现计算逻辑
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
        获取评分分页查询的级联下拉选项

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


def get_scores_service(session: Session) -> ScoresService:
    """获取评分服务实例"""
    return ScoresService(session)
