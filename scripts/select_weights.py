import pandas as pd
import os


def load_and_prepare_data(file_path: str):
    """
    读取并准备权重 Excel 文件。
    使用前向填充 (ffill) 处理因合并单元格产生的空值，以构建完整的层级关系。

    Args:
        file_path (str): Excel 文件的路径。

    Returns:
        pd.DataFrame or None: 处理后的 DataFrame，如果文件不存在或出错则返回 None。
    """
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在。")
        return None

    try:
        print(f"正在读取文件: {file_path}...")
        df = pd.read_excel(file_path)

        # 定义层级列，我们将对这些列进行前向填充
        hierarchy_columns = ["桥梁类型", "部位", "结构类型", "部件类型"]

        # 确保所有预期的列都存在
        for col in hierarchy_columns + ["权重"]:
            if col not in df.columns:
                print(f"错误: Excel 文件中缺少必需的列 '{col}'。")
                return None

        print("正在处理合并单元格（向下填充数据）...")
        # 使用 ffill (forward fill) 向下填充层级列的空值
        df[hierarchy_columns] = df[hierarchy_columns].ffill()

        # 删除可能因格式问题产生的完全为空的行
        df.dropna(how="all", inplace=True)

        print("数据准备完成！")

        return df

    except Exception as e:
        print(f"读取或处理 Excel 文件时发生错误: {e}")
        return None


def build_weight_hierarchy(df: pd.DataFrame):
    """
    将扁平的 DataFrame 构建成一个嵌套的字典（层级结构）。

    Args:
        df (pd.DataFrame): 经过预处理的 DataFrame。

    Returns:
        dict: 代表层级结构的嵌套字典。
              结构: {桥梁类型: {部位: {结构类型: {部件类型: 权重}}}}
    """
    if df is None:
        return {}

    print("正在构建层级查询结构...")
    hierarchy = {}

    # 遍历 DataFrame 的每一行
    for _, row in df.iterrows():
        # 提取每一层的值和最终的权重
        bridge_type = row["桥梁类型"]
        part = row["部位"]
        struct_type = row["结构类型"]
        component_type = row["部件类型"]
        weight = row["权重"]

        # 如果任何一个层级为空或权重为空，则跳过该行
        if (
            pd.isna(bridge_type)
            or pd.isna(part)
            or pd.isna(struct_type)
            or pd.isna(component_type)
            or pd.isna(weight)
        ):
            continue

        # 使用 setdefault 优雅地创建嵌套字典
        current_level = hierarchy.setdefault(bridge_type, {})
        current_level = current_level.setdefault(part, {})
        current_level = current_level.setdefault(struct_type, {})

        # 在最内层设置部件类型和对应的权重
        current_level[component_type] = weight

    print("层级结构构建完成！")
    return hierarchy


def interactive_query(hierarchy: dict):
    """
    提供一个交互式命令行界面，用于逐层查询权重。

    Args:
        hierarchy (dict): 包含权重数据的嵌套字典。
    """
    if not hierarchy:
        print("无法启动查询：层级结构为空。")
        return

    # 定义层级名称
    level_names = ["桥梁类型", "部位", "结构类型", "部件类型"]

    # path 存储用户的选择路径
    path = []
    # current_level 指向当前用户所在层级的字典数据
    current_level_data = hierarchy

    while True:
        # 确定当前是第几层
        current_level_index = len(path)

        if current_level_index == len(level_names):
            break

        print("\n" + "=" * 50)
        print(f"当前路径: {' → '.join(path) if path else '顶层'}")
        print(
            f"【第 {current_level_index + 1} 层】请选择一个 '{level_names[current_level_index]}':"
        )

        # 获取当前层级的选项
        options = list(current_level_data.keys())

        # 显示所有选项
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print("  0. 返回上一层 / 退出")

        try:
            choice_str = input("\n请输入您的选择 (数字): ").strip()
            if not choice_str.isdigit():
                print("输入无效，请输入数字。")
                continue

            choice = int(choice_str)

            if choice == 0:
                if not path:
                    # 在顶层选择0，退出程序
                    print("退出查询系统。")
                    break
                else:
                    # 返回上一层
                    path.pop()
                    # 重置 current_level_data 到上一层
                    current_level_data = hierarchy
                    for step in path:
                        current_level_data = current_level_data[step]
                    continue

            if 1 <= choice <= len(options):
                selected_option = options[choice - 1]
                path.append(selected_option)

                # 移动到下一层级
                next_level_data = current_level_data[selected_option]

                # 检查下一层是字典（更多选项）还是最终的权重值
                if isinstance(next_level_data, dict):
                    current_level_data = next_level_data
                else:
                    # 如果不是字典，说明已到达终点，找到了权重
                    print("\n" + "🎉" * 15)
                    print(f"查询完成！")
                    print(f"完整路径: {' → '.join(path)}")
                    print(f"对应的权重是: {next_level_data}")
                    print("🎉" * 15)

                    # 查询完成后，自动返回上一层，以便用户进行其他查询
                    path.pop()
                    input("\n按回车键继续查询...")

            else:
                print(f"无效选择。请输入 0 到 {len(options)} 之间的数字。")

        except ValueError:
            print("输入无效，请输入一个有效的数字。")
        except KeyboardInterrupt:
            print("\n查询被中断。退出。")
            break


def main():
    """
    主函数，执行整个流程。
    """
    # --- 主要修改部分 ---
    # 动态构建文件的绝对路径，使其不受执行位置的影响

    # 1. 获取当前脚本文件所在的目录 (e.g., /path/to/project/scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. 从脚本目录向上一级，找到项目根目录 (e.g., /path/to/project)
    project_root = os.path.dirname(script_dir)

    # 3. 拼接出 static 文件夹下 Excel 文件的完整路径
    excel_file = os.path.join(project_root, "static", "weight_base.xlsx")
    # --- 修改结束 ---

    # 1. 读取和准备数据
    df = load_and_prepare_data(excel_file)

    if df is not None:
        # 2. 构建层级结构
        hierarchy_data = build_weight_hierarchy(df)

        # 3. 启动交互式查询
        interactive_query(hierarchy_data)


if __name__ == "__main__":
    print("--- 桥梁构件权重分级查询系统 ---")
    print("请确保已安装必要的库: pip install pandas openpyxl")
    print("-" * 50)
    main()
