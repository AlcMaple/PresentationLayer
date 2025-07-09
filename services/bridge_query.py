from sqlmodel import Session, select
from typing import List, Optional
from dataclasses import dataclass

from models import (
    Paths,
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


@dataclass
class BridgePathData:
    """桥梁路径数据类"""

    id: int

    # ID字段
    category_id: Optional[int] = None
    assessment_unit_id: Optional[int] = None
    bridge_type_id: Optional[int] = None
    part_id: Optional[int] = None
    structure_id: Optional[int] = None
    component_type_id: Optional[int] = None
    component_form_id: Optional[int] = None
    disease_id: Optional[int] = None
    scale_id: Optional[int] = None
    quality_id: Optional[int] = None
    quantity_id: Optional[int] = None

    # NAME字段
    category_name: Optional[str] = None
    assessment_unit_name: Optional[str] = None
    bridge_type_name: Optional[str] = None
    part_name: Optional[str] = None
    structure_name: Optional[str] = None
    component_type_name: Optional[str] = None
    component_form_name: Optional[str] = None
    disease_name: Optional[str] = None
    scale_name: Optional[str] = None
    quality_name: Optional[str] = None
    quantity_name: Optional[str] = None

    # CODE字段
    category_code: Optional[str] = None
    assessment_unit_code: Optional[str] = None
    bridge_type_code: Optional[str] = None
    part_code: Optional[str] = None
    structure_code: Optional[str] = None
    component_type_code: Optional[str] = None
    component_form_code: Optional[str] = None
    disease_code: Optional[str] = None
    scale_code: Optional[str] = None
    quality_code: Optional[str] = None
    quantity_code: Optional[str] = None


class BridgeQueryService:
    """桥梁数据查询服务"""

    def __init__(self, session: Session):
        self.session = session

    def get_paths_with_names(
        self, limit: int = 10, offset: int = 0
    ) -> List[BridgePathData]:
        """获取路径数据"""

        statement = (
            select(
                Paths.id,
                Paths.category_id,
                Paths.assessment_unit_id,
                Paths.bridge_type_id,
                Paths.part_id,
                Paths.structure_id,
                Paths.component_type_id,
                Paths.component_form_id,
                Paths.disease_id,
                Paths.scale_id,
                Paths.quality_id,
                Paths.quantity_id,
                # NAME字段
                Categories.name.label("category_name"),
                AssessmentUnit.name.label("assessment_unit_name"),
                BridgeTypes.name.label("bridge_type_name"),
                BridgeParts.name.label("part_name"),
                BridgeStructures.name.label("structure_name"),
                BridgeComponentTypes.name.label("component_type_name"),
                BridgeComponentForms.name.label("component_form_name"),
                BridgeDiseases.name.label("disease_name"),
                BridgeScales.name.label("scale_name"),
                BridgeQualities.name.label("quality_name"),
                BridgeQuantities.name.label("quantity_name"),
                # CODE字段
                Categories.code.label("category_code"),
                AssessmentUnit.code.label("assessment_unit_code"),
                BridgeTypes.code.label("bridge_type_code"),
                BridgeParts.code.label("part_code"),
                BridgeStructures.code.label("structure_code"),
                BridgeComponentTypes.code.label("component_type_code"),
                BridgeComponentForms.code.label("component_form_code"),
                BridgeDiseases.code.label("disease_code"),
                BridgeScales.code.label("scale_code"),
                BridgeQualities.code.label("quality_code"),
                BridgeQuantities.code.label("quantity_code"),
            )
            .outerjoin(Categories, Paths.category_id == Categories.id)
            .outerjoin(AssessmentUnit, Paths.assessment_unit_id == AssessmentUnit.id)
            .outerjoin(BridgeTypes, Paths.bridge_type_id == BridgeTypes.id)
            .outerjoin(BridgeParts, Paths.part_id == BridgeParts.id)
            .outerjoin(BridgeStructures, Paths.structure_id == BridgeStructures.id)
            .outerjoin(
                BridgeComponentTypes,
                Paths.component_type_id == BridgeComponentTypes.id,
            )
            .outerjoin(
                BridgeComponentForms,
                Paths.component_form_id == BridgeComponentForms.id,
            )
            .outerjoin(BridgeDiseases, Paths.disease_id == BridgeDiseases.id)
            .outerjoin(BridgeScales, Paths.scale_id == BridgeScales.id)
            .outerjoin(BridgeQualities, Paths.quality_id == BridgeQualities.id)
            .outerjoin(BridgeQuantities, Paths.quantity_id == BridgeQuantities.id)
            .offset(offset)
            .limit(limit)
        )

        results = self.session.exec(statement).all()

        # 转换数据对象
        path_data_list = []
        for row in results:
            path_data = BridgePathData(
                id=row.id,
                category_id=row.category_id,
                assessment_unit_id=row.assessment_unit_id,
                bridge_type_id=row.bridge_type_id,
                part_id=row.part_id,
                structure_id=row.structure_id,
                component_type_id=row.component_type_id,
                component_form_id=row.component_form_id,
                disease_id=row.disease_id,
                scale_id=row.scale_id,
                quality_id=row.quality_id,
                quantity_id=row.quantity_id,
                # NAME字段
                category_name=row.category_name,
                assessment_unit_name=row.assessment_unit_name,
                bridge_type_name=row.bridge_type_name,
                part_name=row.part_name,
                structure_name=row.structure_name,
                component_type_name=row.component_type_name,
                component_form_name=row.component_form_name,
                disease_name=row.disease_name,
                scale_name=row.scale_name,
                quality_name=row.quality_name,
                quantity_name=row.quantity_name,
                # CODE字段
                category_code=row.category_code,
                assessment_unit_code=row.assessment_unit_code,
                bridge_type_code=row.bridge_type_code,
                part_code=row.part_code,
                structure_code=row.structure_code,
                component_type_code=row.component_type_code,
                component_form_code=row.component_form_code,
                disease_code=row.disease_code,
                scale_code=row.scale_code,
                quality_code=row.quality_code,
                quantity_code=row.quantity_code,
            )
            path_data_list.append(path_data)

        return path_data_list

    def count_total_paths(self) -> int:
        """获取路径总数"""
        statement = select(Paths.id)
        results = self.session.exec(statement).all()
        return len(results)

    def search_by_disease(self, disease_name: str) -> List[BridgePathData]:
        """根据病害类型搜索路径"""
        statement = (
            select(
                Paths.id,
                Paths.category_id,
                Paths.assessment_unit_id,
                Paths.bridge_type_id,
                Paths.part_id,
                Paths.structure_id,
                Paths.component_type_id,
                Paths.component_form_id,
                Paths.disease_id,
                Paths.scale_id,
                Paths.quality_id,
                Paths.quantity_id,
                # NAME字段
                Categories.name.label("category_name"),
                AssessmentUnit.name.label("assessment_unit_name"),
                BridgeTypes.name.label("bridge_type_name"),
                BridgeParts.name.label("part_name"),
                BridgeStructures.name.label("structure_name"),
                BridgeComponentTypes.name.label("component_type_name"),
                BridgeComponentForms.name.label("component_form_name"),
                BridgeDiseases.name.label("disease_name"),
                BridgeScales.name.label("scale_name"),
                BridgeQualities.name.label("quality_name"),
                BridgeQuantities.name.label("quantity_name"),
                # CODE字段
                Categories.code.label("category_code"),
                AssessmentUnit.code.label("assessment_unit_code"),
                BridgeTypes.code.label("bridge_type_code"),
                BridgeParts.code.label("part_code"),
                BridgeStructures.code.label("structure_code"),
                BridgeComponentTypes.code.label("component_type_code"),
                BridgeComponentForms.code.label("component_form_code"),
                BridgeDiseases.code.label("disease_code"),
                BridgeScales.code.label("scale_code"),
                BridgeQualities.code.label("quality_code"),
                BridgeQuantities.code.label("quantity_code"),
            )
            .outerjoin(Categories, Paths.category_id == Categories.id)
            .outerjoin(AssessmentUnit, Paths.assessment_unit_id == AssessmentUnit.id)
            .outerjoin(BridgeTypes, Paths.bridge_type_id == BridgeTypes.id)
            .outerjoin(BridgeParts, Paths.part_id == BridgeParts.id)
            .outerjoin(BridgeStructures, Paths.structure_id == BridgeStructures.id)
            .outerjoin(
                BridgeComponentTypes,
                Paths.component_type_id == BridgeComponentTypes.id,
            )
            .outerjoin(
                BridgeComponentForms,
                Paths.component_form_id == BridgeComponentForms.id,
            )
            .outerjoin(BridgeDiseases, Paths.disease_id == BridgeDiseases.id)
            .outerjoin(BridgeScales, Paths.scale_id == BridgeScales.id)
            .outerjoin(BridgeQualities, Paths.quality_id == BridgeQualities.id)
            .outerjoin(BridgeQuantities, Paths.quantity_id == BridgeQuantities.id)
            .where(BridgeDiseases.name == disease_name)
        )

        results = self.session.exec(statement).all()

        path_data_list = []
        for row in results:
            path_data = BridgePathData(
                id=row.id,
                category_id=row.category_id,
                assessment_unit_id=row.assessment_unit_id,
                bridge_type_id=row.bridge_type_id,
                part_id=row.part_id,
                structure_id=row.structure_id,
                component_type_id=row.component_type_id,
                component_form_id=row.component_form_id,
                disease_id=row.disease_id,
                scale_id=row.scale_id,
                quality_id=row.quality_id,
                quantity_id=row.quantity_id,
                # NAME字段
                category_name=row.category_name,
                assessment_unit_name=row.assessment_unit_name,
                bridge_type_name=row.bridge_type_name,
                part_name=row.part_name,
                structure_name=row.structure_name,
                component_type_name=row.component_type_name,
                component_form_name=row.component_form_name,
                disease_name=row.disease_name,
                scale_name=row.scale_name,
                quality_name=row.quality_name,
                quantity_name=row.quantity_name,
                # CODE字段
                category_code=row.category_code,
                assessment_unit_code=row.assessment_unit_code,
                bridge_type_code=row.bridge_type_code,
                part_code=row.part_code,
                structure_code=row.structure_code,
                component_type_code=row.component_type_code,
                component_form_code=row.component_form_code,
                disease_code=row.disease_code,
                scale_code=row.scale_code,
                quality_code=row.quality_code,
                quantity_code=row.quantity_code,
            )
            path_data_list.append(path_data)

        return path_data_list


def get_bridge_query_service(session: Session) -> BridgeQueryService:
    """获取桥梁查询服务实例"""
    return BridgeQueryService(session)
