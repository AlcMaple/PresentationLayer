from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, and_
from datetime import datetime, timezone

from models import (
    InspectionRecords,
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
)
from models.enums import ScalesType
from schemas.inspection_records import (
    InspectionRecordsCreate,
    InspectionRecordsUpdate,
    InspectionRecordsResponse,
    PathValidationRequest,
    FormOptionsResponse,
    DamageTypeOption,
    ScaleOption,
)
from services.base_crud import BaseCRUDService, PageParams
from exceptions import ValidationException, NotFoundException


class InspectionRecordsService(
    BaseCRUDService[InspectionRecords, InspectionRecordsCreate, InspectionRecordsUpdate]
):
    """检查记录服务"""

    def __init__(self, session: Session):
        super().__init__(InspectionRecords, session)

    def _validate_path_exists(self, path_request: PathValidationRequest) -> bool:
        """
        验证前7层路径是否在paths表中存在
        """
        try:
            # 构建查询条件
            conditions = [
                Paths.category_id == path_request.category_id,
                Paths.bridge_type_id == path_request.bridge_type_id,
                Paths.part_id == path_request.part_id,
                Paths.component_type_id == path_request.component_type_id,
                Paths.component_form_id == path_request.component_form_id,
                Paths.is_active == True,
            ]

            if path_request.assessment_unit_id:
                conditions.append(
                    Paths.assessment_unit_id == path_request.assessment_unit_id
                )
            else:
                conditions.append(Paths.assessment_unit_id.is_(None))

            if path_request.structure_id:
                conditions.append(Paths.structure_id == path_request.structure_id)
            else:
                conditions.append(Paths.structure_id.is_(None))

            stmt = select(Paths.id).where(and_(*conditions)).limit(1)
            result = self.session.exec(stmt).first()

            return result is not None

        except Exception as e:
            print(f"验证路径时出错: {e}")
            return False

    def get_scales_by_damage_type(
        self, path_request: PathValidationRequest, damage_type_code: str
    ) -> List[ScaleOption]:
        """
        根据病害类型获取对应的标度选项
        """
        try:
            # 获取病害类型ID
            damage_type_id = self._get_id_by_code(BridgeDiseases, damage_type_code)
            if not damage_type_id:
                return []

            # 构建查询条件
            conditions = [
                Paths.category_id == path_request.category_id,
                Paths.bridge_type_id == path_request.bridge_type_id,
                Paths.part_id == path_request.part_id,
                Paths.component_type_id == path_request.component_type_id,
                Paths.component_form_id == path_request.component_form_id,
                Paths.disease_id == damage_type_id,
                Paths.is_active == True,
            ]

            if path_request.assessment_unit_id:
                conditions.append(
                    Paths.assessment_unit_id == path_request.assessment_unit_id
                )
            else:
                conditions.append(Paths.assessment_unit_id.is_(None))

            if path_request.structure_id:
                conditions.append(Paths.structure_id == path_request.structure_id)
            else:
                conditions.append(Paths.structure_id.is_(None))

            # 查询对应的标度
            stmt = select(Paths.scale_id).where(and_(*conditions)).distinct()
            scale_ids = self.session.exec(stmt).all()

            if scale_ids:
                scale_stmt = (
                    select(
                        BridgeScales.code,
                        BridgeScales.name,
                        BridgeScales.scale_type,
                        BridgeScales.scale_value,
                        BridgeScales.min_value,
                        BridgeScales.max_value,
                        BridgeScales.unit,
                        BridgeScales.display_text,
                    )
                    .where(
                        and_(
                            BridgeScales.id.in_(scale_ids),
                            BridgeScales.is_active == True,
                        )
                    )
                    .order_by(BridgeScales.scale_value)
                )

                scale_results = self.session.exec(scale_stmt).all()

                options = []
                for result in scale_results:
                    (
                        code,
                        name,
                        scale_type,
                        scale_value,
                        min_value,
                        max_value,
                        unit,
                        display_text,
                    ) = result

                    # 根据标度类型构建显示名称
                    if scale_type == ScalesType.NUMERIC:
                        display_name = (
                            str(scale_value) if scale_value is not None else name
                        )
                        value = scale_value
                    elif scale_type == ScalesType.RANGE:
                        if min_value is not None and max_value is not None and unit:
                            display_name = f"{min_value}-{max_value}{unit}"
                        else:
                            display_name = name
                        value = None
                    elif scale_type == ScalesType.TEXT:
                        display_name = display_text if display_text else name
                        value = None
                    else:
                        display_name = name
                        value = scale_value

                    options.append(
                        ScaleOption(code=code, name=display_name, value=value)
                    )

                return options

            return []

        except Exception as e:
            print(f"获取标度选项时出错: {e}")
            return []

    def create(self, record_data: InspectionRecordsCreate) -> InspectionRecordsResponse:
        """
        创建检查记录
        """
        try:
            # 验证路径是否存在
            path_request = PathValidationRequest(
                category_id=record_data.category_id,
                assessment_unit_id=record_data.assessment_unit_id,
                bridge_type_id=record_data.bridge_type_id,
                part_id=record_data.part_id,
                structure_id=record_data.structure_id,
                component_type_id=record_data.component_type_id,
                component_form_id=record_data.component_form_id,
            )

            if not self._validate_path_exists(path_request):
                raise ValidationException("指定的路径组合在系统中不存在")

            # 验证病害类型和标度的组合是否有效
            if not self._validate_damage_scale_combination(
                path_request, record_data.damage_type_code, record_data.scale_code
            ):
                raise ValidationException("指定的病害类型和标度组合无效")

            # 创建检查记录
            inspection_record = InspectionRecords(
                category_id=record_data.category_id,
                assessment_unit_id=record_data.assessment_unit_id,
                bridge_type_id=record_data.bridge_type_id,
                part_id=record_data.part_id,
                structure_id=record_data.structure_id,
                component_type_id=record_data.component_type_id,
                component_form_id=record_data.component_form_id,
                damage_type_code=record_data.damage_type_code,
                scale_code=record_data.scale_code,
                damage_location=record_data.damage_location,
                damage_description=record_data.damage_description,
                image_url=record_data.image_url,
            )

            self.session.add(inspection_record)
            self.session.commit()
            self.session.refresh(inspection_record)

            # 返回详细信息
            return self.get_record_with_details(inspection_record.id)

        except ValidationException:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"创建检查记录失败: {str(e)}")

    def get_record_with_details(self, record_id: int) -> InspectionRecordsResponse:
        """
        获取包含详细关联信息的检查记录
        """
        try:
            # 查询基础记录
            stmt = select(InspectionRecords).where(
                and_(
                    InspectionRecords.id == record_id,
                    InspectionRecords.is_active == True,
                )
            )
            record = self.session.exec(stmt).first()

            if not record:
                raise NotFoundException(
                    resource="InspectionRecords", identifier=str(record_id)
                )

            # 获取关联信息
            details = self._get_record_related_data(record)

            # 构建响应
            return InspectionRecordsResponse(
                id=record.id,
                category_id=record.category_id,
                category_name=details.get("category_name"),
                assessment_unit_id=record.assessment_unit_id,
                assessment_unit_name=details.get("assessment_unit_name"),
                bridge_type_id=record.bridge_type_id,
                bridge_type_name=details.get("bridge_type_name"),
                part_id=record.part_id,
                part_name=details.get("part_name"),
                structure_id=record.structure_id,
                structure_name=details.get("structure_name"),
                component_type_id=record.component_type_id,
                component_type_name=details.get("component_type_name"),
                component_form_id=record.component_form_id,
                component_form_name=details.get("component_form_name"),
                damage_type_code=record.damage_type_code,
                damage_type_name=details.get("damage_type_name"),
                scale_code=record.scale_code,
                scale_name=details.get("scale_name"),
                scale_value=details.get("scale_value"),
                damage_location=record.damage_location,
                damage_description=record.damage_description,
                image_url=record.image_url,
                created_at=record.created_at,
                updated_at=record.updated_at,
                is_active=record.is_active,
            )

        except NotFoundException:
            raise
        except Exception as e:
            raise Exception(f"获取检查记录详情失败: {str(e)}")

    def _get_id_by_code(self, model_class, code: str) -> Optional[int]:
        """
        通过code获取ID
        """
        try:
            stmt = select(model_class.id).where(
                and_(model_class.code == code, model_class.is_active == True)
            )
            return self.session.exec(stmt).first()
        except:
            return None

    def _get_damage_type_options(self, base_conditions: List) -> List[DamageTypeOption]:
        """
        获取病害类型选项
        """
        try:
            # 查询该路径下所有的病害类型ID
            stmt = select(Paths.disease_id).where(and_(*base_conditions)).distinct()
            disease_ids = self.session.exec(stmt).all()

            if disease_ids:
                # 获取病害类型详细信息
                disease_stmt = (
                    select(BridgeDiseases.code, BridgeDiseases.name)
                    .where(
                        and_(
                            BridgeDiseases.id.in_(disease_ids),
                            BridgeDiseases.is_active == True,
                        )
                    )
                    .order_by(BridgeDiseases.code)
                )

                disease_results = self.session.exec(disease_stmt).all()

                return [
                    DamageTypeOption(code=result[0], name=result[1])
                    for result in disease_results
                ]

            return []
        except Exception as e:
            print(f"获取病害类型选项时出错: {e}")
            return []

    def _get_scale_options(self, base_conditions: List) -> List[ScaleOption]:
        """
        获取标度选项
        """
        try:
            # 查询该路径下所有的标度ID
            stmt = select(Paths.scale_id).where(and_(*base_conditions)).distinct()
            scale_ids = self.session.exec(stmt).all()

            if scale_ids:
                # 获取标度详细信息
                scale_stmt = (
                    select(
                        BridgeScales.code, BridgeScales.name, BridgeScales.scale_value
                    )
                    .where(
                        and_(
                            BridgeScales.id.in_(scale_ids),
                            BridgeScales.is_active == True,
                        )
                    )
                    .order_by(BridgeScales.scale_value)
                )

                scale_results = self.session.exec(scale_stmt).all()

                return [
                    ScaleOption(code=result[0], name=result[1], value=result[2])
                    for result in scale_results
                ]

            return []
        except Exception as e:
            print(f"获取标度选项时出错: {e}")
            return []

    def _validate_damage_scale_combination(
        self,
        path_request: PathValidationRequest,
        damage_type_code: str,
        scale_code: str,
    ) -> bool:
        """
        验证病害类型和标度的组合是否在paths表中存在
        """
        try:
            # 获取病害类型和标度的ID
            damage_type_id = self._get_id_by_code(BridgeDiseases, damage_type_code)
            scale_id = self._get_id_by_code(BridgeScales, scale_code)

            if not damage_type_id or not scale_id:
                return False

            # 构建完整查询条件
            conditions = [
                Paths.category_id == path_request.category_id,
                Paths.bridge_type_id == path_request.bridge_type_id,
                Paths.part_id == path_request.part_id,
                Paths.component_type_id == path_request.component_type_id,
                Paths.component_form_id == path_request.component_form_id,
                Paths.disease_id == damage_type_id,
                Paths.scale_id == scale_id,
                Paths.is_active == True,
            ]

            if path_request.assessment_unit_id:
                conditions.append(
                    Paths.assessment_unit_id == path_request.assessment_unit_id
                )
            else:
                conditions.append(Paths.assessment_unit_id.is_(None))

            if path_request.structure_id:
                conditions.append(Paths.structure_id == path_request.structure_id)
            else:
                conditions.append(Paths.structure_id.is_(None))

            stmt = select(Paths.id).where(and_(*conditions)).limit(1)
            result = self.session.exec(stmt).first()

            return result is not None

        except Exception as e:
            print(f"验证病害标度组合时出错: {e}")
            return False

    def _get_record_related_data(self, record: InspectionRecords) -> Dict[str, Any]:
        """
        获取检查记录的关联数据
        """
        details = {}

        # 定义查询映射
        field_mappings = [
            ("category_id", Categories, "category"),
            ("assessment_unit_id", AssessmentUnit, "assessment_unit"),
            ("bridge_type_id", BridgeTypes, "bridge_type"),
            ("part_id", BridgeParts, "part"),
            ("structure_id", BridgeStructures, "structure"),
            ("component_type_id", BridgeComponentTypes, "component_type"),
            ("component_form_id", BridgeComponentForms, "component_form"),
        ]

        for field_name, model_class, prefix in field_mappings:
            field_id = getattr(record, field_name, None)
            if field_id:
                try:
                    stmt = select(model_class.name).where(model_class.id == field_id)
                    result = self.session.exec(stmt).first()
                    details[f"{prefix}_name"] = result
                except:
                    details[f"{prefix}_name"] = None
            else:
                details[f"{prefix}_name"] = None

        # 获取病害类型信息
        try:
            stmt = select(BridgeDiseases.name).where(
                BridgeDiseases.code == record.damage_type_code
            )
            details["damage_type_name"] = self.session.exec(stmt).first()
        except:
            details["damage_type_name"] = None

        # 获取标度信息
        try:
            stmt = select(
                BridgeScales.name,
                BridgeScales.scale_type,
                BridgeScales.scale_value,
                BridgeScales.min_value,
                BridgeScales.max_value,
                BridgeScales.unit,
                BridgeScales.display_text,
            ).where(BridgeScales.code == record.scale_code)
            scale_result = self.session.exec(stmt).first()
            if scale_result:
                (
                    name,
                    scale_type,
                    scale_value,
                    min_value,
                    max_value,
                    unit,
                    display_text,
                ) = scale_result

                # 根据标度类型构建显示名称
                if scale_type == ScalesType.NUMERIC:
                    display_name = str(scale_value) if scale_value is not None else name
                    details["scale_value"] = scale_value
                elif scale_type == ScalesType.RANGE:
                    if min_value is not None and max_value is not None and unit:
                        display_name = f"{min_value}-{max_value}{unit}"
                    else:
                        display_name = name
                    details["scale_value"] = None
                elif scale_type == ScalesType.TEXT:
                    display_name = display_text if display_text else name
                    details["scale_value"] = None
                else:
                    display_name = name
                    details["scale_value"] = scale_value

                details["scale_name"] = display_name
            else:
                details["scale_name"] = None
                details["scale_value"] = None
        except:
            details["scale_name"] = None
            details["scale_value"] = None

        return details

    def update(
        self, record_id: int, update_data: InspectionRecordsUpdate
    ) -> InspectionRecordsResponse:
        """
        更新检查记录

        Args:
            record_id: 记录ID
            update_data: 更新数据
        """
        try:
            # 查询现有记录
            existing_record = self.get_by_id(record_id)
            if not existing_record:
                raise NotFoundException(
                    resource="InspectionRecords", identifier=str(record_id)
                )

            # 如果更新了病害类型或标度，需要验证组合的有效性
            if update_data.damage_type_code or update_data.scale_code:
                # 构建路径验证请求
                path_request = PathValidationRequest(
                    category_id=existing_record.category_id,
                    assessment_unit_id=existing_record.assessment_unit_id,
                    bridge_type_id=existing_record.bridge_type_id,
                    part_id=existing_record.part_id,
                    structure_id=existing_record.structure_id,
                    component_type_id=existing_record.component_type_id,
                    component_form_id=existing_record.component_form_id,
                )

                # 确定最终的病害类型和标度编码
                final_damage_code = (
                    update_data.damage_type_code or existing_record.damage_type_code
                )
                final_scale_code = update_data.scale_code or existing_record.scale_code

                # 验证病害类型和标度的组合
                if not self._validate_damage_scale_combination(
                    path_request, final_damage_code, final_scale_code
                ):
                    raise ValidationException("指定的病害类型和标度组合无效")

            # 更新字段
            if update_data.damage_type_code is not None:
                existing_record.damage_type_code = update_data.damage_type_code
            if update_data.scale_code is not None:
                existing_record.scale_code = update_data.scale_code
            if update_data.damage_location is not None:
                existing_record.damage_location = update_data.damage_location
            if update_data.damage_description is not None:
                existing_record.damage_description = update_data.damage_description
            if update_data.image_url is not None:
                existing_record.image_url = update_data.image_url

            # 更新时间
            existing_record.updated_at = datetime.now(timezone.utc)

            # 保存更改
            self.session.commit()
            self.session.refresh(existing_record)

            # 返回详细信息
            return self.get_record_with_details(record_id)

        except (NotFoundException, ValidationException):
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise Exception(f"更新检查记录失败: {str(e)}")


def get_inspection_records_service(session: Session) -> InspectionRecordsService:
    """获取检查记录服务实例"""
    return InspectionRecordsService(session)
