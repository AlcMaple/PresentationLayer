import json
import sys
import os
from sqlmodel import Session, select
from typing import Dict, Optional, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
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
    Paths,
)


class PathImporter:
    """路径数据导入器"""

    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.session = Session(engine)

        # 缓存字典 - 避免重复查询
        self.name_to_id_cache = {
            "categories": {},
            "assessment_units": {},
            "bridge_types": {},
            "parts": {},
            "structures": {},
            "component_types": {},
            "component_forms": {},
            "diseases": {},
            "scales": {},
            "qualities": {},
            "quantities": {},
        }

        # 统计信息
        self.stats = {
            "total_paths": 0,
            "success_paths": 0,
            "error_paths": 0,
            "errors": [],
        }

    def load_json_data(self) -> Dict:
        """加载JSON数据"""
        print(f"正在加载JSON文件: {self.json_file_path}")
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("JSON文件加载成功")
            return data
        except Exception as e:
            print(f"加载JSON文件失败: {e}")
            raise

    def build_cache(self):
        """构建name到id的缓存映射"""
        print("正在构建缓存映射...")

        # 分类
        categories = self.session.exec(select(Categories)).all()
        for cat in categories:
            self.name_to_id_cache["categories"][cat.name] = cat.id

        # 评定单元
        units = self.session.exec(select(AssessmentUnit)).all()
        for unit in units:
            self.name_to_id_cache["assessment_units"][unit.name] = unit.id

        # 桥梁类型
        bridge_types = self.session.exec(select(BridgeTypes)).all()
        for bt in bridge_types:
            self.name_to_id_cache["bridge_types"][bt.name] = bt.id

        # 部位
        parts = self.session.exec(select(BridgeParts)).all()
        for part in parts:
            self.name_to_id_cache["parts"][part.name] = part.id

        # 结构类型
        structures = self.session.exec(select(BridgeStructures)).all()
        for structure in structures:
            self.name_to_id_cache["structures"][structure.name] = structure.id

        # 部件类型
        component_types = self.session.exec(select(BridgeComponentTypes)).all()
        for ct in component_types:
            self.name_to_id_cache["component_types"][ct.name] = ct.id

        # 构件形式
        component_forms = self.session.exec(select(BridgeComponentForms)).all()
        for cf in component_forms:
            self.name_to_id_cache["component_forms"][cf.name] = cf.id

        # 病害类型
        diseases = self.session.exec(select(BridgeDiseases)).all()
        for disease in diseases:
            self.name_to_id_cache["diseases"][disease.name] = disease.id

        # 标度
        scales = self.session.exec(select(BridgeScales)).all()
        for scale in scales:
            self.name_to_id_cache["scales"][scale.name] = scale.id

        # 定性描述
        qualities = self.session.exec(select(BridgeQualities)).all()
        for quality in qualities:
            self.name_to_id_cache["qualities"][quality.name] = quality.id

        # 定量描述
        quantities = self.session.exec(select(BridgeQuantities)).all()
        for quantity in quantities:
            self.name_to_id_cache["quantities"][quantity.name] = quantity.id

        print("缓存构建完成")
        for key, cache in self.name_to_id_cache.items():
            print(f"  {key}: {len(cache)} 条记录")

    def get_id_by_name(self, table_type: str, name: str) -> Optional[int]:
        """通过名称获取ID"""
        if name == "-" or name is None or name == "":
            return None
        return self.name_to_id_cache[table_type].get(name)

    def process_json_data(self, data: Dict):
        """处理JSON数据，提取路径"""
        print("开始处理JSON数据...")

        self.category_id = self.get_id_by_name("categories", "公路桥")
        self.assessment_unit_id = self.get_id_by_name("assessment_units", "-")

        sheets = data.get("sheets", {})

        for sheet_name, sheet_data in sheets.items():
            print(f"\n处理工作表: {sheet_name}")

            bridge_types = sheet_data.get("bridge_types", {})

            for bridge_type_name, bridge_type_data in bridge_types.items():
                print(f"  处理桥梁类型: {bridge_type_name}")

                bridge_type_id = self.get_id_by_name("bridge_types", bridge_type_name)
                if bridge_type_id is None:
                    print(f"    警告: 未找到桥梁类型 '{bridge_type_name}' 的ID")
                    continue

                # 递归处理部位
                parts = bridge_type_data.get("parts", {})
                self.process_parts(bridge_type_id, parts)

    def process_parts(self, bridge_type_id: int, parts: Dict):
        """处理部位层级"""
        for part_name, part_data in parts.items():
            part_id = self.get_id_by_name("parts", part_name)

            # 处理结构类型
            children = part_data.get("children", {})
            self.process_structures(bridge_type_id, part_id, children)

    def process_structures(
        self, bridge_type_id: int, part_id: Optional[int], structures: Dict
    ):
        """处理结构类型层级"""
        for structure_name, structure_data in structures.items():
            structure_id = self.get_id_by_name("structures", structure_name)

            # 处理部件类型
            children = structure_data.get("children", {})
            self.process_component_types(
                bridge_type_id, part_id, structure_id, children
            )

    def process_component_types(
        self,
        bridge_type_id: int,
        part_id: Optional[int],
        structure_id: Optional[int],
        component_types: Dict,
    ):
        """处理部件类型层级"""
        for component_type_name, component_type_data in component_types.items():
            component_type_id = self.get_id_by_name(
                "component_types", component_type_name
            )

            # 处理构件形式
            children = component_type_data.get("children", {})
            self.process_component_forms(
                bridge_type_id, part_id, structure_id, component_type_id, children
            )

    def process_component_forms(
        self,
        bridge_type_id: int,
        part_id: Optional[int],
        structure_id: Optional[int],
        component_type_id: Optional[int],
        component_forms: Dict,
    ):
        """处理构件形式层级"""
        for component_form_name, component_form_data in component_forms.items():
            component_form_id = self.get_id_by_name(
                "component_forms", component_form_name
            )

            # 处理病害类型
            damage_types = component_form_data.get("damage_types", {})
            self.process_damage_types(
                bridge_type_id,
                part_id,
                structure_id,
                component_type_id,
                component_form_id,
                damage_types,
            )

    def process_damage_types(
        self,
        bridge_type_id: int,
        part_id: Optional[int],
        structure_id: Optional[int],
        component_type_id: Optional[int],
        component_form_id: Optional[int],
        damage_types: Dict,
    ):
        """处理病害类型层级"""
        for disease_name, scale_data_list in damage_types.items():
            disease_id = self.get_id_by_name("diseases", disease_name)

            if disease_id is None:
                print(f"      警告: 未找到病害类型 '{disease_name}' 的ID")
                continue

            # 处理标度数据数组
            for scale_item in scale_data_list:
                self.stats["total_paths"] += 1

                try:
                    # 获取标度、定性、定量描述的ID
                    scale_value = scale_item.get("scale")
                    scale_name = f"标度{scale_value}" if scale_value else None
                    scale_id = (
                        self.get_id_by_name("scales", scale_name)
                        if scale_name
                        else None
                    )

                    qualitative_desc = scale_item.get("qualitative_description", "")
                    quality_id = self.get_id_by_name("qualities", qualitative_desc)

                    quantitative_desc = scale_item.get("quantitative_description", "")
                    quantity_id = self.get_id_by_name("quantities", quantitative_desc)

                    # 创建路径记录
                    path_record = Paths(
                        category_id=self.category_id,
                        assessment_unit_id=self.assessment_unit_id,
                        bridge_type_id=bridge_type_id,
                        part_id=part_id,
                        structure_id=structure_id,
                        component_type_id=component_type_id,
                        component_form_id=component_form_id,
                        disease_id=disease_id,
                        scale_id=scale_id,
                        quality_id=quality_id,
                        quantity_id=quantity_id,
                    )

                    self.session.add(path_record)
                    self.stats["success_paths"] += 1

                    if self.stats["total_paths"] % 100 == 0:
                        print(f"      已处理 {self.stats['total_paths']} 条路径")

                except Exception as e:
                    self.stats["error_paths"] += 1
                    error_msg = (
                        f"处理路径失败: {e}, 病害: {disease_name}, 标度: {scale_item}"
                    )
                    self.stats["errors"].append(error_msg)
                    print(f"      错误: {error_msg}")

    def run_import(self, limit_sheets: int = 1):
        """执行导入流程"""
        try:
            print("开始桥梁路径数据导入...")

            # 1. 加载JSON数据
            data = self.load_json_data()

            # 2. 构建缓存
            self.build_cache()

            # 3. 限制处理的工作表数量（测试用）
            if limit_sheets > 0:
                sheets = list(data.get("sheets", {}).items())[:limit_sheets]
                data["sheets"] = dict(sheets)
                print(f"限制处理前 {limit_sheets} 个工作表进行测试")

            # 4. 处理数据
            self.process_json_data(data)

            # 5. 提交事务
            self.session.commit()

            print("\n✅ 路径数据导入完成!")
            print(f"总路径数: {self.stats['total_paths']}")
            print(f"成功导入: {self.stats['success_paths']}")
            print(f"失败数量: {self.stats['error_paths']}")

            if self.stats["errors"]:
                print("\n错误详情:")
                for error in self.stats["errors"][:5]:  # 只显示前5个错误
                    print(f"  {error}")
                if len(self.stats["errors"]) > 5:
                    print(f"  ... 还有 {len(self.stats['errors']) - 5} 个错误")

        except Exception as e:
            print(f"❌ 导入过程中发生错误: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()


def main():
    """主函数"""
    # JSON文件路径
    json_file = "static/json_output/all_bridge_data_adjusted.json"

    if not os.path.exists(json_file):
        print(f"❌ JSON文件不存在: {json_file}")
        return

    # 执行导入 - 只处理第一个工作表进行测试
    importer = PathImporter(json_file)
    importer.run_import(limit_sheets=1)


if __name__ == "__main__":
    main()
