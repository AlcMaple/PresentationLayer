from typing import List, Dict, Any
from sqlmodel import Session, select, and_, update
from datetime import datetime

from models.paths import Paths


class PathCascadeService:
    """路径级联删除服务"""

    def __init__(self, session: Session):
        self.session = session

        # 定义表名到paths字段的映射关系
        self.table_field_mapping = {
            "categories": "category_id",
            "assessment_units": "assessment_unit_id",
            "bridge_types": "bridge_type_id",
            "bridge_parts": "part_id",
            "bridge_structures": "structure_id",
            "bridge_component_types": "component_type_id",
            "bridge_component_forms": "component_form_id",
            "bridge_diseases": "disease_id",
            "bridge_scales": "scale_id",
            "bridge_qualities": "quality_id",
            "bridge_quantities": "quantity_id",
        }

    def cascade_delete_by_table(self, table_name: str, record_id: int) -> int:
        """
        根据表名和记录ID级联删除paths表中的相关记录

        Args:
            table_name: 基础表名
            record_id: 被删除的记录ID
        """
        # 获取对应的字段名
        field_name = self.table_field_mapping.get(table_name)
        if not field_name:
            raise ValueError(f"未知的表名: {table_name}")

        return self._cascade_delete_by_field(field_name, record_id)

    def _cascade_delete_by_field(self, field_name: str, field_value: int) -> int:
        """
        根据字段名和值级联删除

        Args:
            field_name: paths表中的字段名
            field_value: 字段值
        """
        try:
            # 构建更新语句
            stmt = (
                update(Paths)
                .where(
                    and_(
                        getattr(Paths, field_name) == field_value,
                        Paths.is_active == True,
                    )
                )
                .values(is_active=False, updated_at=datetime.utcnow())
            )

            # 更新
            result = self.session.execute(stmt)
            affected_rows = result.rowcount

            # 提交事务
            self.session.commit()

            print(
                f"级联删除: {field_name}={field_value}, 影响 {affected_rows} 条路径记录"
            )
            return affected_rows

        except Exception as e:
            self.session.rollback()
            print(f"级联删除失败: {e}")
            raise
        
def get_path_cascade_service(session: Session) -> PathCascadeService:
    """获取路径级联删除服务实例"""
    return PathCascadeService(session)
