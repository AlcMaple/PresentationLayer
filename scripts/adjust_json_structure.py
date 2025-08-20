import json
import os
import re
from datetime import datetime


class BridgeJsonAdjuster:
    """桥梁JSON数据结构调整器"""

    def __init__(self):
        self.separator = "、"  # 顿号分隔符

    def split_by_separator(self, text):
        """按顿号分割文本"""
        if not text or text.strip() == "-":
            return [text] if text else ["-"]

        # 分割并清理空字符串
        parts = [part.strip() for part in text.split(self.separator) if part.strip()]
        return parts if parts else [text]

    def parse_scale_data(self, scale_str, qualitative_str, quantitative_str):
        """解析标度相关数据，返回数组格式"""
        # 分割各部分
        scales = self.split_by_separator(scale_str)
        qualitatives = self.split_by_separator(qualitative_str)
        quantitatives = self.split_by_separator(quantitative_str)

        # 确保数量一致，如果不一致则用最长的补齐
        max_len = max(len(scales), len(qualitatives), len(quantitatives))

        # 补齐数组长度
        while len(scales) < max_len:
            scales.append(scales[-1] if scales else "-")
        while len(qualitatives) < max_len:
            qualitatives.append(qualitatives[-1] if qualitatives else "-")
        while len(quantitatives) < max_len:
            quantitatives.append(quantitatives[-1] if quantitatives else "-")

        # 构建数组
        result = []
        for i in range(max_len):
            # 尝试从标度字符串中提取数字
            scale_value = i + 1  # 默认从1开始
            if i < len(scales):
                # 尝试提取数字
                numbers = re.findall(r"\d+", scales[i])
                if numbers:
                    scale_value = int(numbers[0])

            result.append(
                {
                    "scale": scale_value,
                    "qualitative_description": qualitatives[i],
                    "quantitative_description": quantitatives[i],
                }
            )

        return result

    def process_damage_types(self, damage_data):
        """处理病害类型数据"""
        processed_data = {}

        for damage_name, damage_info in damage_data.items():
            if not isinstance(damage_info, dict):
                continue

            # 分割病害类型名称
            damage_names = self.split_by_separator(damage_name)

            # 处理details中的数据
            if "children" in damage_info and "details" in damage_info["children"]:
                details = damage_info["children"]["details"]

                # 为每个分割的病害类型创建相同的数据
                for single_damage_name in damage_names:
                    processed_data[single_damage_name] = self.process_details(details)

        return processed_data

    def process_details(self, details):
        """处理details数据，转换为数组格式"""
        result_array = []

        for scale_key, scale_data in details.items():
            if not isinstance(scale_data, dict):
                continue

            scale_str = scale_data.get("scale", scale_key)
            qualitative_descriptions = scale_data.get("qualitative_descriptions", {})

            for qual_desc, qual_data in qualitative_descriptions.items():
                quantitative_descriptions = qual_data.get(
                    "quantitative_descriptions", {}
                )

                for quan_desc, _ in quantitative_descriptions.items():
                    # 解析并添加到结果数组
                    parsed_data = self.parse_scale_data(scale_str, qual_desc, quan_desc)
                    result_array.extend(parsed_data)

        # 去重并按scale排序
        unique_data = {}
        for item in result_array:
            scale = item["scale"]
            if scale not in unique_data:
                unique_data[scale] = item

        # 转换为按scale排序的数组
        sorted_data = []
        for scale in sorted(unique_data.keys()):
            sorted_data.append(unique_data[scale])

        return sorted_data

    def split_hierarchical_keys(self, data_dict, target_levels=None):
        """
        对指定层级的keys进行顿号分割处理

        Args:
            data_dict: 要处理的字典
            target_levels: 需要分割的层级列表，如果为None则处理所有支持的层级

        Returns:
            处理后的字典
        """
        if target_levels is None:
            target_levels = ["部件类型", "构件形式", "病害类型"]

        processed_data = {}

        for key, value in data_dict.items():
            if not isinstance(value, dict):
                processed_data[key] = value
                continue

            current_level = value.get("level", "")

            # 检查是否需要对当前层级进行分割处理
            if current_level in target_levels:
                # 分割key
                split_keys = self.split_by_separator(key)

                # 为每个分割的key创建相同的数据结构
                for split_key in split_keys:
                    new_value = value.copy()
                    new_value["name"] = split_key  # 更新名称为分割后的值
                    processed_data[split_key] = new_value
            else:
                # 不需要分割，直接复制
                processed_data[key] = value

        return processed_data

    def adjust_recursive_structure(self, data, current_level_name=""):
        """递归调整数据结构，支持所有层级的顿号分割"""
        if not isinstance(data, dict):
            return data

        # 首先对当前层级的keys进行顿号分割处理
        split_data = self.split_hierarchical_keys(data)
        adjusted_data = {}

        for key, value in split_data.items():
            if not isinstance(value, dict):
                adjusted_data[key] = value
                continue

            current_level = value.get("level", "")

            # 检查是否到达构件形式级别
            if current_level == "构件形式":
                # 这是构件形式级别，需要特殊处理
                adjusted_data[key] = {
                    "name": value.get("name", key),
                    "level": value.get("level"),
                    "record_count": value.get("record_count", 0),
                    "damage_types": {},
                }

                # 处理子级的病害类型
                if "children" in value:
                    damage_types_data = {}
                    for child_name, child_data in value["children"].items():
                        if (
                            isinstance(child_data, dict)
                            and child_data.get("level") == "病害类型"
                        ):
                            damage_types_data[child_name] = child_data

                    adjusted_data[key]["damage_types"] = self.process_damage_types(
                        damage_types_data
                    )

            elif "children" in value:
                # 其他级别，继续递归处理
                adjusted_data[key] = {
                    "name": value.get("name", key),
                    "level": value.get("level", ""),
                    "record_count": value.get("record_count", 0),
                    "children": self.adjust_recursive_structure(
                        value["children"], value.get("level", "")
                    ),
                }
            else:
                # 叶子节点，直接复制
                adjusted_data[key] = value

        return adjusted_data

    def adjust_component_forms(self, component_forms):
        """调整构件形式级别的数据"""
        adjusted_forms = {}

        for form_name, form_data in component_forms.items():
            if not isinstance(form_data, dict):
                continue

            adjusted_forms[form_name] = {
                "name": form_data.get("name", form_name),
                "level": form_data.get("level", "构件形式"),
                "record_count": form_data.get("record_count", 0),
                "damage_types": {},
            }

            # 处理病害类型
            if "children" in form_data:
                damage_types_data = {}
                for child_name, child_data in form_data["children"].items():
                    if child_name != "details" and isinstance(child_data, dict):
                        damage_types_data[child_name] = child_data

                adjusted_forms[form_name]["damage_types"] = self.process_damage_types(
                    damage_types_data
                )

        return adjusted_forms

    def adjust_json_file(self, input_file, output_file=None):
        """调整JSON文件结构"""
        if not os.path.exists(input_file):
            print(f"错误: 输入文件 {input_file} 不存在")
            return None

        # 确定输出文件名
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_adjusted.json"

        print(f"正在调整文件: {input_file}")

        try:
            # 读取原始JSON数据
            with open(input_file, "r", encoding="utf-8") as f:
                original_data = json.load(f)

            # 调整数据结构
            adjusted_data = {
                "metadata": {
                    "original_file": input_file,
                    "adjusted_time": datetime.now().isoformat(),
                    "original_metadata": original_data.get("metadata", {}),
                    "structure_version": "2.1",
                    "description": "调整后的桥梁数据结构，所有层级都支持顿号分割，标度数据使用数组格式",
                }
            }

            # 处理工作表数据
            if "sheets" in original_data:
                adjusted_data["sheets"] = {}
                for sheet_name, sheet_data in original_data["sheets"].items():
                    print(f"  处理工作表: {sheet_name}")
                    adjusted_data["sheets"][sheet_name] = {
                        "metadata": sheet_data.get("metadata", {}),
                        "bridge_types": {},
                    }

                    # 处理桥梁类型数据
                    if "bridge_types" in sheet_data:
                        for bridge_type, bridge_data in sheet_data[
                            "bridge_types"
                        ].items():
                            print(f"    处理桥梁类型: {bridge_type}")
                            adjusted_data["sheets"][sheet_name]["bridge_types"][
                                bridge_type
                            ] = {
                                "name": bridge_data.get("name", bridge_type),
                                "record_count": bridge_data.get("record_count", 0),
                                "parts": self.adjust_recursive_structure(
                                    bridge_data.get("parts", {})
                                ),
                            }

            elif "bridge_types" in original_data:
                # 直接处理桥梁类型数据
                adjusted_data["bridge_types"] = {}
                for bridge_type, bridge_data in original_data["bridge_types"].items():
                    print(f"  处理桥梁类型: {bridge_type}")
                    adjusted_data["bridge_types"][bridge_type] = {
                        "name": bridge_data.get("name", bridge_type),
                        "record_count": bridge_data.get("record_count", 0),
                        "parts": self.adjust_recursive_structure(
                            bridge_data.get("parts", {})
                        ),
                    }

            # 保存调整后的数据
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(adjusted_data, f, ensure_ascii=False, indent=2)

            print(f"✓ 调整完成，已保存到: {output_file}")

            # 显示统计信息
            self.print_adjustment_summary(original_data, adjusted_data)

            return adjusted_data

        except Exception as e:
            print(f"调整文件时出错: {e}")
            import traceback

            traceback.print_exc()
            return None

    def print_adjustment_summary(self, original_data, adjusted_data):
        """打印调整摘要"""
        print(f"\n{'='*50}")
        print("调整摘要:")
        print("=" * 50)

        # 统计原始数据
        original_sheets = len(original_data.get("sheets", {}))
        if original_sheets == 0 and "bridge_types" in original_data:
            original_sheets = 1

        # 统计调整后数据
        adjusted_sheets = len(adjusted_data.get("sheets", {}))
        if adjusted_sheets == 0 and "bridge_types" in adjusted_data:
            adjusted_sheets = 1

        print(f"• 处理的工作表数量: {original_sheets}")
        print(f"• 数据结构版本: 2.1 (支持所有层级顿号分割和数组格式标度)")
        print(f"• 主要改进:")
        print(
            f"  - 所有层级（部位、结构类型、部件类型、构件形式、病害类型）均支持顿号分割"
        )
        print(f"  - 标度、定性描述、定量描述转换为对应数组")
        print(f"  - 每个标度值对应明确的描述信息")
        print(f"  - 分割后的项目保持独立的数据结构")
        print("=" * 50)

    def adjust_all_files_in_directory(
        self, input_dir="json_output", output_dir="json_output_adjusted"
    ):
        """调整目录中的所有JSON文件"""
        if not os.path.exists(input_dir):
            print(f"错误: 输入目录 {input_dir} 不存在")
            return

        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 找到所有JSON文件
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]

        if not json_files:
            print(f"在目录 {input_dir} 中没有找到JSON文件")
            return

        print(f"找到 {len(json_files)} 个JSON文件")

        for json_file in json_files:
            input_path = os.path.join(input_dir, json_file)
            output_path = os.path.join(output_dir, json_file)

            print(f"\n处理文件: {json_file}")
            self.adjust_json_file(input_path, output_path)

        print(f"\n✅ 所有文件处理完成！")
        print(f"📁 调整后的文件保存在: {output_dir}/")


def main():
    """主函数"""
    print("=" * 60)
    print("桥梁JSON数据结构调整工具")
    print("=" * 60)

    adjuster = BridgeJsonAdjuster()

    # 提供选择
    print("请选择处理方式:")
    print("1. 处理单个JSON文件")
    print("2. 处理整个目录的JSON文件")
    print("0. 退出")

    choice = input("\n请输入选择 (数字): ").strip()

    if choice == "1":
        # 处理单个文件
        input_file = input("请输入要调整的JSON文件路径: ").strip()
        if not input_file:
            input_file = "static/json_output/all_bridge_data.json"  # 默认文件

        output_file = input("请输入输出文件路径 (回车使用默认): ").strip()
        if not output_file:
            output_file = None

        adjuster.adjust_json_file(input_file, output_file)

    elif choice == "2":
        # 处理整个目录
        input_dir = input(
            "请输入包含JSON文件的目录路径 (回车使用默认 json_output): "
        ).strip()
        if not input_dir:
            input_dir = "json_output"

        output_dir = input(
            "请输入输出目录路径 (回车使用默认 json_output_adjusted): "
        ).strip()
        if not output_dir:
            output_dir = "json_output_adjusted"

        adjuster.adjust_all_files_in_directory(input_dir, output_dir)

    elif choice == "0":
        print("程序退出")

    else:
        print("无效选择")


if __name__ == "__main__":
    main()
