import pandas as pd
import json
import os
from datetime import datetime


class WeightDataJsonConverter:
    """
    将 'weight_base.xlsx' 中的层级权重数据转换为结构化的 JSON 文件。
    借鉴了 BridgeDataJsonConverter 的设计模式，但针对更简单的权重结构进行了优化。
    """

    def __init__(self, file_path: str, output_path: str):
        """
        初始化转换器。

        Args:
            file_path (str): 输入的 Excel 文件路径。
            output_path (str): 输出的 JSON 文件路径。
        """
        self.file_path = file_path
        self.output_path = output_path
        # 定义权重文件的层级结构
        self.hierarchy_columns = ["桥梁类型", "部位", "结构类型", "部件类型"]
        print(f"输入文件: {self.file_path}")
        print(f"计划输出: {self.output_path}")

    def _load_and_prepare_data(self) -> pd.DataFrame or None:
        """
        [内部方法] 读取并准备 Excel 数据。
        使用前向填充 (ffill) 处理合并单元格。
        """
        if not os.path.exists(self.file_path):
            print(f"错误: 文件 '{self.file_path}' 不存在。")
            return None
        try:
            print("正在读取和准备数据...")
            df = pd.read_excel(self.file_path)

            # 确保所有必需列存在
            for col in self.hierarchy_columns + ["权重"]:
                if col not in df.columns:
                    print(f"错误: Excel 文件中缺少必需的列 '{col}'。")
                    return None

            # 向下填充层级列的空值
            df[self.hierarchy_columns] = df[self.hierarchy_columns].ffill()
            df.dropna(subset=["权重"], inplace=True)  # 删除没有权重的行
            print("数据准备完成。")
            return df
        except Exception as e:
            print(f"读取或处理 Excel 文件时发生错误: {e}")
            return None

    def _build_recursive_json(
        self, data: pd.DataFrame, current_dict: dict, hierarchy_levels: list
    ):
        """
        [内部方法] 递归构建 JSON 的层级结构。
        """
        # 如果是最后一层 (部件类型)，则直接添加权重信息，停止递归
        if len(hierarchy_levels) == 1:
            last_level_name = hierarchy_levels[0]
            for _, row in data.iterrows():
                component_name = row[last_level_name]
                weight = row["权重"]
                if pd.notna(component_name) and pd.notna(weight):
                    current_dict[component_name] = {
                        "name": component_name,
                        "level": last_level_name,
                        "weight": weight,
                    }
            return

        current_level_name = hierarchy_levels[0]
        remaining_levels = hierarchy_levels[1:]

        # 获取当前层级的所有唯一值
        unique_values = data[current_level_name].dropna().unique()

        for value in unique_values:
            filtered_data = data[data[current_level_name] == value]

            current_dict[value] = {
                "name": value,
                "level": current_level_name,
                "record_count": len(filtered_data),
                "children": {},
            }
            # 递归进入下一层
            self._build_recursive_json(
                filtered_data, current_dict[value]["children"], remaining_levels
            )

    def convert_to_json(self):
        """
        执行转换过程，并将最终的 JSON 数据保存到文件。
        """
        df = self._load_and_prepare_data()
        if df is None:
            print("因数据加载失败，转换中止。")
            return

        print("开始构建 JSON 结构...")
        # 初始化最终的 JSON 结构，包含元数据
        final_json = {
            "metadata": {
                "source_file": os.path.basename(self.file_path),
                "export_time": datetime.now().isoformat(),
                "total_records": len(df),
            },
            "bridge_types": {},
        }

        # 按顶层“桥梁类型”进行分组
        top_level_groups = df.groupby("桥梁类型")

        for bridge_type, group_data in top_level_groups:
            print(f"  - 正在处理桥梁类型: {bridge_type}")
            final_json["bridge_types"][bridge_type] = {
                "name": bridge_type,
                "level": "桥梁类型",
                "record_count": len(group_data),
                "children": {},
            }
            # 从“部位”层级开始递归构建
            self._build_recursive_json(
                group_data,
                final_json["bridge_types"][bridge_type]["children"],
                self.hierarchy_columns[1:],  # 从第二个层级开始
            )

        print("JSON 结构构建完成。")

        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(self.output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"已创建输出目录: {output_dir}")

            # 将字典写入 JSON 文件
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(final_json, f, ensure_ascii=False, indent=2)

            print("\n" + "=" * 50)
            print(f"✅ 成功！JSON 文件已保存到:")
            print(f"   {self.output_path}")
            print("=" * 50)

        except Exception as e:
            print(f"保存 JSON 文件时出错: {e}")


def main():
    """主函数，负责设置路径并启动转换器。"""
    print("--- 权重数据 JSON 转换工具 ---")

    # 动态构建输入和输出文件的路径，使其不受执行位置的影响
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # 输入文件路径
    excel_file = os.path.join(project_root, "static", "weight_base.xlsx")

    # 输出文件路径
    output_json_file = os.path.join(
        project_root, "static", "json_output", "weights.json"
    )

    # 创建并运行转换器
    converter = WeightDataJsonConverter(
        file_path=excel_file, output_path=output_json_file
    )
    converter.convert_to_json()


if __name__ == "__main__":
    main()
