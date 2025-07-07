import pandas as pd
import os


def merge_same_groups():
    """
    读取合并后的Excel文件，按A列分组，将B、C、D列用顿号合并
    """
    # 输入文件名
    input_file = "合并后的ABCD列数据.xlsx"

    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：找不到输入文件 '{input_file}'")
        print("请先运行第一个脚本生成合并数据文件！")
        return

    try:
        # 读取Excel文件
        print(f"📖 正在读取文件: {input_file}")
        df = pd.read_excel(input_file, sheet_name="合并数据")

        print(f"📊 原始数据: {len(df)} 行")

        # 显示原始数据预览
        print(f"\n📋 原始数据预览（前5行）：")
        print(df.head())

        # 检查必要的列是否存在
        required_columns = ["A", "B", "C", "D"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"错误：缺少必要的列：{missing_columns}")
            return

        # 清理数据：将NaN和空值转换为空字符串
        for col in ["A", "B", "C", "D"]:
            df[col] = df[col].fillna("").astype(str).str.strip()

        # 删除A列为空的行
        df = df[df["A"] != ""].copy()

        if df.empty:
            print("错误：没有有效的数据可以处理（A列全为空）")
            return

        print(f"📊 清理后数据: {len(df)} 行")

        # 按A列分组并合并B、C、D列
        print(f"\n🔄 开始按A列分组合并...")

        def join_non_empty_values(series):
            """合并非空值，用顿号分隔"""
            # 过滤掉空字符串和'nan'字符串
            values = [
                str(val).strip()
                for val in series
                if str(val).strip() != "" and str(val).strip().lower() != "nan"
            ]
            if values:
                return "、".join(values)
            else:
                return ""

        # 分组聚合
        grouped_data = df.groupby("A", as_index=False).agg(
            {
                "B": join_non_empty_values,
                "C": join_non_empty_values,
                "D": join_non_empty_values,
                "文件来源": lambda x: "、".join(
                    sorted(set(str(val) for val in x if str(val).strip() != ""))
                ),
            }
        )

        print(f"📊 合并后数据: {len(grouped_data)} 组")

        # 显示合并后的数据预览
        print(f"\n📋 合并后数据预览：")
        print(grouped_data.head())

        # 输出文件名
        output_file = "按A列分组合并后的数据.xlsx"

        # 保存结果到新的Excel文件
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # 保存分组合并后的数据
            grouped_data.to_excel(writer, sheet_name="分组合并数据", index=False)

            # 同时保存原始数据供参考
            df.to_excel(writer, sheet_name="原始数据", index=False)

        print(f"\n✅ 成功！")
        print(f"💾 输出文件：{output_file}")
        print(f"📁 包含两个工作表：")
        print(f"   - '分组合并数据'：按A列分组合并的结果")
        print(f"   - '原始数据'：处理前的原始数据")

        # 显示详细统计
        print(f"\n📈 分组统计：")

        # 统计每个A列值有多少行原始数据
        original_counts = df["A"].value_counts()
        print(f"📊 原始数据中各A列值的行数分布：")
        for value, count in original_counts.head(10).items():
            # 截断过长的文本用于显示
            display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"  '{display_value}': {count} 行")

        if len(original_counts) > 10:
            print(f"  ... 还有 {len(original_counts) - 10} 个分组")

        # 显示B、C、D列的合并情况
        print(f"\n📋 合并情况概览：")
        print(
            f"  B列有内容的分组: {(grouped_data['B'] != '').sum()} / {len(grouped_data)}"
        )
        print(
            f"  C列有内容的分组: {(grouped_data['C'] != '').sum()} / {len(grouped_data)}"
        )
        print(
            f"  D列有内容的分组: {(grouped_data['D'] != '').sum()} / {len(grouped_data)}"
        )

        # 显示一个具体的合并示例
        if len(grouped_data) > 0:
            example_row = grouped_data.iloc[0]
            print(f"\n📝 合并示例：")
            print(f"  A列: {example_row['A']}")
            print(
                f"  B列: {example_row['B'][:100]}{'...' if len(str(example_row['B'])) > 100 else ''}"
            )
            print(
                f"  C列: {example_row['C'][:100]}{'...' if len(str(example_row['C'])) > 100 else ''}"
            )
            print(
                f"  D列: {example_row['D'][:100]}{'...' if len(str(example_row['D'])) > 100 else ''}"
            )

    except Exception as e:
        print(f"✗ 处理过程中发生错误：{e}")
        import traceback

        traceback.print_exc()


def main():
    """
    主函数
    """
    print("🔄 开始按A列分组合并数据...")
    print("-" * 60)

    # 检查是否安装了openpyxl
    try:
        import openpyxl
    except ImportError:
        print("⚠️ 缺少依赖库！请先安装：")
        print("pip install openpyxl")
        return

    merge_same_groups()

    print("-" * 60)
    print("🏁 脚本执行完成！")


if __name__ == "__main__":
    main()
