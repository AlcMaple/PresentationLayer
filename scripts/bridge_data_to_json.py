import pandas as pd
import json
import os
from datetime import datetime


class BridgeDataJsonConverter:
    """桥梁数据JSON转换器"""

    def __init__(self, file_path):
        self.file_path = file_path
        self.hierarchy_columns = [
            "桥梁类型",
            "部位",
            "结构类型",
            "部件类型",
            "构件形式",
            "病害类型",
            "标度",
            "定性描述",
            "定量描述",
        ]

    def get_available_sheets(self):
        """获取所有可用的工作表"""
        try:
            excel_data = pd.read_excel(self.file_path, sheet_name=None)
            return list(excel_data.keys())
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return []

    def extract_hierarchical_structure(self, sheet_name):
        """提取层级关系结构"""
        try:
            # 读取工作表
            df = pd.read_excel(self.file_path, sheet_name=sheet_name, header=None)

            print(f"正在处理工作表: {sheet_name}")
            print(f"数据形状: {df.shape}")

            if df is None or len(df) < 2:
                print("数据行数不足")
                return None

            # 使用第二行作为列标题，从第三行开始是数据
            header_row = df.iloc[1].fillna("")
            data_df = df.iloc[2:].copy()
            data_df.columns = header_row

            # 清理列名
            clean_columns = []
            for col in data_df.columns:
                if pd.isna(col) or col == "":
                    clean_columns.append(f"未命名_{len(clean_columns)}")
                else:
                    clean_columns.append(str(col))

            data_df.columns = clean_columns

            # 确保我们有足够的列，映射到标准列名
            expected_columns = self.hierarchy_columns
            if len(data_df.columns) >= len(expected_columns):
                data_df.columns = expected_columns + list(
                    data_df.columns[len(expected_columns) :]
                )
            else:
                data_df.columns = expected_columns[: len(data_df.columns)]

            # 重置索引
            data_df = data_df.reset_index(drop=True)

            # 处理合并单元格 - 向下填充空值
            hierarchy_cols = expected_columns[:6]  # 到病害类型为止
            for col in hierarchy_cols:
                if col in data_df.columns:
                    data_df[col] = data_df[col].replace("", pd.NA)
                    data_df[col] = data_df[col].where(data_df[col].notna(), pd.NA)
                    data_df[col] = data_df[col].fillna(method="ffill")

            print(f"处理后的数据行数: {len(data_df)}")

            # 构建JSON结构
            json_structure = self.build_json_structure(data_df)

            return json_structure

        except Exception as e:
            print(f"提取层级结构时出错: {e}")
            import traceback

            traceback.print_exc()
            return None

    def build_json_structure(self, data_df):
        """构建JSON结构"""
        result = {
            "metadata": {
                "export_time": datetime.now().isoformat(),
                "total_records": len(data_df),
                "columns": list(data_df.columns),
            },
            "bridge_types": {},
        }

        # 按桥梁类型分组
        bridge_types = data_df["桥梁类型"].dropna().unique()
        bridge_types = [
            bt for bt in bridge_types if str(bt).strip() and str(bt) != "nan"
        ]

        print(f"发现的桥梁类型: {bridge_types}")

        for bridge_type in bridge_types:
            print(f"处理桥梁类型: {bridge_type}")
            bridge_data = data_df[data_df["桥梁类型"] == bridge_type].copy()

            result["bridge_types"][bridge_type] = {
                "name": bridge_type,
                "record_count": len(bridge_data),
                "parts": {},
            }

            # 构建递归结构
            self.build_recursive_json(
                bridge_data,
                result["bridge_types"][bridge_type]["parts"],
                ["部位", "结构类型", "部件类型", "构件形式", "病害类型"],
                ["标度", "定性描述", "定量描述"],
            )

        return result

    def build_recursive_json(self, data, current_dict, hierarchy_levels, detail_levels):
        """递归构建JSON结构"""
        if not hierarchy_levels:
            # 到达最深层，构建详细信息
            self.build_detail_json(data, current_dict, detail_levels)
            return

        current_level = hierarchy_levels[0]
        remaining_levels = hierarchy_levels[1:]

        # 获取当前层级的所有唯一值
        unique_values = data[current_level].dropna().unique()
        unique_values = [
            val for val in unique_values if str(val).strip() and str(val) != "nan"
        ]

        for value in unique_values:
            filtered_data = data[data[current_level] == value]

            current_dict[value] = {
                "name": value,
                "level": current_level,
                "record_count": len(filtered_data),
                "children": {} if remaining_levels else {"details": {}},
            }

            if remaining_levels:
                self.build_recursive_json(
                    filtered_data,
                    current_dict[value]["children"],
                    remaining_levels,
                    detail_levels,
                )
            else:
                self.build_detail_json(
                    filtered_data,
                    current_dict[value]["children"]["details"],
                    detail_levels,
                )

    def build_detail_json(self, data, current_dict, detail_levels):
        """构建详细信息的JSON结构"""
        # 处理标度
        scale_values = data["标度"].dropna().unique()
        scale_values = [
            val for val in scale_values if str(val).strip() and str(val) != "nan"
        ]

        for scale in scale_values:
            scale_data = data[data["标度"] == scale]
            current_dict[str(scale)] = {
                "scale": str(scale),
                "qualitative_descriptions": {},
            }

            # 处理定性描述
            qual_values = scale_data["定性描述"].dropna().unique()
            qual_values = [
                val for val in qual_values if str(val).strip() and str(val) != "nan"
            ]

            for qual_desc in qual_values:
                qual_data = scale_data[scale_data["定性描述"] == qual_desc]
                current_dict[str(scale)]["qualitative_descriptions"][str(qual_desc)] = {
                    "description": str(qual_desc),
                    "quantitative_descriptions": {},
                }

                # 处理定量描述
                quan_values = qual_data["定量描述"].dropna().unique()
                quan_values = [
                    val for val in quan_values if str(val).strip() and str(val) != "nan"
                ]

                for quan_desc in quan_values:
                    current_dict[str(scale)]["qualitative_descriptions"][
                        str(qual_desc)
                    ]["quantitative_descriptions"][str(quan_desc)] = {
                        "description": str(quan_desc),
                        "is_complete": True,
                    }

    def convert_all_sheets_to_json(self, output_dir="json_output"):
        """转换所有工作表为JSON文件"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        sheet_names = self.get_available_sheets()
        if not sheet_names:
            print("没有找到可用的工作表")
            return

        all_sheets_data = {
            "metadata": {
                "source_file": self.file_path,
                "export_time": datetime.now().isoformat(),
                "total_sheets": len(sheet_names),
                "sheet_names": sheet_names,
            },
            "sheets": {},
        }

        for sheet_name in sheet_names:
            print(f"\n{'='*50}")
            print(f"正在转换工作表: {sheet_name}")
            print("=" * 50)

            try:
                # 提取该工作表的数据
                sheet_data = self.extract_hierarchical_structure(sheet_name)

                if sheet_data:
                    # 保存单个工作表的JSON文件
                    sheet_filename = (
                        f"{sheet_name.replace('/', '_').replace('—', '_')}.json"
                    )
                    sheet_filepath = os.path.join(output_dir, sheet_filename)

                    with open(sheet_filepath, "w", encoding="utf-8") as f:
                        json.dump(sheet_data, f, ensure_ascii=False, indent=2)

                    print(f"✓ 已保存: {sheet_filepath}")

                    # 添加到总数据中
                    all_sheets_data["sheets"][sheet_name] = sheet_data

                else:
                    print(f"✗ 工作表 {sheet_name} 数据提取失败")

            except Exception as e:
                print(f"✗ 处理工作表 {sheet_name} 时出错: {e}")

        # 保存包含所有工作表的总JSON文件
        all_sheets_filepath = os.path.join(output_dir, "all_bridge_data.json")
        with open(all_sheets_filepath, "w", encoding="utf-8") as f:
            json.dump(all_sheets_data, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*50}")
        print(f"✓ 所有数据已保存到: {all_sheets_filepath}")
        print(f"✓ 单独的工作表文件保存在: {output_dir} 目录")
        print("=" * 50)

        return all_sheets_data


def main():
    """主函数"""
    excel_file = "utils/work.xls"

    if not os.path.exists(excel_file):
        print(f"错误: 文件 {excel_file} 不存在")
        print("请确保文件在当前目录下")
        return

    print("=" * 60)
    print("桥梁数据JSON转换工具")
    print("=" * 60)

    # 创建转换器
    converter = BridgeDataJsonConverter(excel_file)

    try:
        # 转换所有工作表
        all_data = converter.convert_all_sheets_to_json()

        if all_data:
            print(f"\n✅ 转换完成!")
            print(f"📁 输出目录: json_output/")
            print(f"📄 主文件: json_output/all_bridge_data.json")
            # 显示统计信息
            total_bridge_types = len(all_data.get("sheets", {}))
            print(f"\n📊 统计信息:")
            print(f"   • 处理的工作表数量: {total_bridge_types}")

            for sheet_name, sheet_data in all_data.get("sheets", {}).items():
                bridge_types = len(sheet_data.get("bridge_types", {}))
                total_records = sheet_data.get("metadata", {}).get("total_records", 0)
                print(
                    f"   • {sheet_name}: {bridge_types}种桥梁类型, {total_records}条记录"
                )

        else:
            print("❌ 没有成功转换任何数据")

    except Exception as e:
        print(f"❌ 转换过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
