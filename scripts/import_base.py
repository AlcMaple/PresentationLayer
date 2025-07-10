import json
import sys
import os
from typing import Set, Dict, List
from sqlmodel import Session

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from models import (
    BridgeTypes,
    BridgeParts,
    BridgeStructures,
    BridgeComponentTypes,
    BridgeComponentForms,
    BridgeDiseases,
    BridgeScales,
    BridgeQualities,
    BridgeQuantities,
    Categories,
    AssessmentUnit,
)
from services.code_generator import get_code_generator


class BridgeDataImporter:
    """桥梁数据导入器"""

    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.session = Session(engine)
        self.code_generator = get_code_generator(self.session)

        # 用于去重的集合
        self.bridge_types: Set[str] = set()
        self.parts: Set[str] = set()
        self.structures: Set[str] = set()
        self.component_types: Set[str] = set()
        self.component_forms: Set[str] = set()
        self.hazards: Set[str] = set()
        self.scales: Set[int] = set()
        self.qualities: Set[str] = set()
        self.quantities: Set[str] = set()

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

    def extract_data_from_json(self, data: Dict):
        """从JSON中提取所有基础数据"""
        print("开始提取基础数据...")

        sheets = data.get("sheets", {})

        for sheet_name, sheet_data in sheets.items():
            print(f"处理工作表: {sheet_name}")

            bridge_types = sheet_data.get("bridge_types", {})

            for bridge_type_name, bridge_type_data in bridge_types.items():
                # 桥梁类型
                self.bridge_types.add(bridge_type_name)

                parts = bridge_type_data.get("parts", {})

                for part_name, part_data in parts.items():
                    # 部位
                    self.parts.add(part_name)

                    children = part_data.get("children", {})

                    for structure_name, structure_data in children.items():
                        # 结构类型
                        self.structures.add(structure_name)

                        structure_children = structure_data.get("children", {})

                        for (
                            comp_type_name,
                            comp_type_data,
                        ) in structure_children.items():
                            # 部件类型
                            self.component_types.add(comp_type_name)

                            comp_children = comp_type_data.get("children", {})

                            for comp_form_name, comp_form_data in comp_children.items():
                                # 构件形式 - 只有当它有damage_types时才是真正的构件形式
                                if "damage_types" in comp_form_data:
                                    self.component_forms.add(comp_form_name)

                                    # 病害类型和标度数据
                                    damage_types = comp_form_data.get(
                                        "damage_types", {}
                                    )

                                    for (
                                        hazard_name,
                                        scale_data_list,
                                    ) in damage_types.items():
                                        # 病害类型
                                        self.hazards.add(hazard_name)

                                        # 标度数据
                                        for scale_item in scale_data_list:
                                            if isinstance(scale_item, dict):
                                                # 标度值
                                                scale_val = scale_item.get("scale")
                                                if scale_val is not None:
                                                    self.scales.add(int(scale_val))

                                                # 定性描述
                                                qual_desc = scale_item.get(
                                                    "qualitative_description"
                                                )
                                                if (
                                                    qual_desc
                                                    and qual_desc.strip()
                                                    and qual_desc != "-"
                                                ):
                                                    self.qualities.add(
                                                        qual_desc.strip()
                                                    )

                                                # 定量描述 - 修改过滤条件，允许"-"
                                                quan_desc = scale_item.get(
                                                    "quantitative_description"
                                                )
                                                if quan_desc and quan_desc.strip():
                                                    self.quantities.add(
                                                        quan_desc.strip()
                                                    )
                                else:
                                    # 如果没有damage_types，可能需要继续向下遍历
                                    print(
                                        f"警告: {comp_form_name} 没有damage_types，可能是数据结构异常"
                                    )

        print("数据提取完成")
        print(f"桥梁类型: {len(self.bridge_types)} 个")
        print(f"部位: {len(self.parts)} 个")
        print(f"结构类型: {len(self.structures)} 个")
        print(f"部件类型: {len(self.component_types)} 个")
        print(f"构件形式: {len(self.component_forms)} 个")
        print(f"病害类型: {len(self.hazards)} 个")
        print(f"标度: {len(self.scales)} 个")
        print(f"定性描述: {len(self.qualities)} 个")
        print(f"定量描述: {len(self.quantities)} 个")

    def import_bridge_types(self):
        """导入桥梁类型"""
        print("导入桥梁类型...")
        for idx, name in enumerate(sorted(self.bridge_types), 1):
            # 使用新的编码生成器
            code = self.code_generator.generate_code("bridge_types")

            bridge_type = BridgeTypes(
                name=name,
                code=code,
                description=f"{name}类型桥梁",
                sort_order=idx,
            )
            self.session.add(bridge_type)
            self.session.commit()
        print(f"成功导入 {len(self.bridge_types)} 个桥梁类型")

    def import_parts(self):
        """导入部位"""
        print("导入部位...")
        for idx, name in enumerate(sorted(self.parts), 1):
            code = self.code_generator.generate_code("bridge_parts")

            part = BridgeParts(
                name=name,
                code=code,
                description=f"{name}部位",
                sort_order=idx,
            )
            self.session.add(part)
            self.session.commit()
        print(f"成功导入 {len(self.parts)} 个部位")

    def import_structures(self):
        """导入结构类型"""
        print("导入结构类型...")
        for idx, name in enumerate(sorted(self.structures), 1):
            code = self.code_generator.generate_code("bridge_structures")

            structure = BridgeStructures(
                name=name,
                code=code,
                description=f"{name}结构",
                sort_order=idx,
            )
            self.session.add(structure)
            self.session.commit()
        print(f"成功导入 {len(self.structures)} 个结构类型")

    def import_component_types(self):
        """导入部件类型"""
        print("导入部件类型...")
        for idx, name in enumerate(sorted(self.component_types), 1):
            code = self.code_generator.generate_code("bridge_component_types")

            comp_type = BridgeComponentTypes(
                name=name,
                code=code,
                description=f"{name}部件",
                sort_order=idx,
            )
            self.session.add(comp_type)
            self.session.commit()
        print(f"成功导入 {len(self.component_types)} 个部件类型")

    def import_component_forms(self):
        """导入构件形式"""
        print("导入构件形式...")
        for idx, name in enumerate(sorted(self.component_forms), 1):
            code = self.code_generator.generate_code("bridge_component_forms")

            comp_form = BridgeComponentForms(
                name=name,
                code=code,
                description=f"{name}构件",
                sort_order=idx,
            )
            self.session.add(comp_form)
            self.session.commit()
        print(f"成功导入 {len(self.component_forms)} 个构件形式")

    def import_hazards(self):
        """导入病害类型"""
        print("导入病害类型...")
        for idx, name in enumerate(sorted(self.hazards), 1):
            code = self.code_generator.generate_code("bridge_diseases")

            hazard = BridgeDiseases(
                name=name,
                code=code,
                description=f"{name}病害",
                sort_order=idx,
            )
            self.session.add(hazard)
            self.session.commit()
        print(f"成功导入 {len(self.hazards)} 个病害类型")

    def import_scales(self):
        """导入标度"""
        print("导入标度...")
        from models.enums import ScalesType

        for scale_val in sorted(self.scales):
            code = self.code_generator.generate_code("bridge_scales")

            scale = BridgeScales(
                name=f"标度{scale_val}",
                code=code,
                description=f"标度等级{scale_val}",
                scale_type=ScalesType.NUMERIC,
                scale_value=scale_val,
                sort_order=scale_val,
            )
            self.session.add(scale)
            self.session.commit()
        print(f"成功导入 {len(self.scales)} 个标度")

    def import_qualities(self):
        """导入定性描述"""
        print("导入定性描述...")
        for idx, desc in enumerate(sorted(self.qualities), 1):
            code = self.code_generator.generate_code("bridge_qualities")

            quality = BridgeQualities(
                name=desc,
                code=code,
                description=desc,
                sort_order=idx,
            )
            self.session.add(quality)
            self.session.commit()
        print(f"成功导入 {len(self.qualities)} 个定性描述")

    def import_quantities(self):
        """导入定量描述"""
        print("导入定量描述...")
        for idx, desc in enumerate(sorted(self.quantities), 1):
            code = self.code_generator.generate_code("bridge_quantities")

            quantity = BridgeQuantities(
                name=desc,
                code=code,
                description=desc,
                sort_order=idx,
            )
            self.session.add(quantity)
            self.session.commit()
        print(f"成功导入 {len(self.quantities)} 个定量描述")

    def import_categories(self):
        """导入分类数据"""
        print("导入分类...")
        category_names = ["公路桥", "城市桥"]
        for idx, name in enumerate(category_names, 1):
            code = self.code_generator.generate_code("categories")
            category = Categories(
                name=name,
                code=code,
                description=f"{name}分类",
                # parent_id=None,
                level=0,
                sort_order=idx,
                is_active=True,
            )
            self.session.add(category)
            self.session.commit()
        print(f"成功导入 {len(category_names)} 个分类")

    def import_assessment_unit(self):
        """导入评定单元（空数据）"""
        print("导入评定单元...")
        code = self.code_generator.generate_code("assessment_units")
        unit = AssessmentUnit(
            name="-",
            code=code,
            description=None,
            sort_order=0,
            is_active=True,
        )
        self.session.add(unit)
        self.session.commit()
        print("成功导入 1 个评定单元（空数据）")

    def run_import(self):
        """执行完整的导入流程"""
        try:
            print("开始桥梁数据导入...")

            # 1. 加载JSON数据
            data = self.load_json_data()

            # 2. 提取基础数据
            self.extract_data_from_json(data)

            # 3. 按顺序导入各个基础表，每一部分单独try，避免全部中断
            steps = [
                ("桥梁类型", self.import_bridge_types),
                ("部位", self.import_parts),
                ("结构类型", self.import_structures),
                ("部件类型", self.import_component_types),
                ("构件形式", self.import_component_forms),
                ("病害类型", self.import_hazards),
                ("标度", self.import_scales),
                ("定性描述", self.import_qualities),
                ("定量描述", self.import_quantities),
                ("分类", self.import_categories),
                ("评定单元", self.import_assessment_unit),
            ]

            for name, func in steps:
                try:
                    print(f"🚀 正在导入: {name}")
                    func()
                except Exception as e:
                    print(f"❌ 导入 {name} 失败: {e}")
                    self.session.rollback()

            print("✅ 桥梁数据导入完成!")

        except Exception as e:
            print(f"❌ 导入过程中发生严重错误: {e}")
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

    # 执行导入
    importer = BridgeDataImporter(json_file)
    importer.run_import()


if __name__ == "__main__":
    main()
