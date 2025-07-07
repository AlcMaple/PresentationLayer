import pandas as pd
import os
import glob


def read_csv_with_encoding(file_path):
    """
    尝试使用不同编码读取CSV文件
    """
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "cp936", "latin1"]

    for encoding in encodings:
        try:
            # header=None 确保第一行不被当作列名，而是当作数据
            df = pd.read_csv(file_path, encoding=encoding, header=None)
            return df, encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            continue

    raise Exception(f"无法使用任何编码读取文件")


def concat_csv_first_four_columns():
    """
    拼接"病害标度描述"目录下所有CSV文件的前4列数据
    """
    # 目录路径
    folder_path = "病害标度描述"

    # 检查目录是否存在
    if not os.path.exists(folder_path):
        print(f"错误：目录 '{folder_path}' 不存在！")
        return

    # 获取目录下所有CSV文件
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    if not csv_files:
        print(f"错误：在目录 '{folder_path}' 中没有找到CSV文件！")
        return

    print(f"找到 {len(csv_files)} 个CSV文件")

    # 存储所有数据的列表
    all_data = []

    # 遍历每个CSV文件
    for i, file_path in enumerate(csv_files, 1):
        try:
            # 尝试使用不同编码读取CSV文件
            df, used_encoding = read_csv_with_encoding(file_path)

            # 检查文件是否有数据
            if df.empty:
                print(
                    f"○ 跳过空文件: {os.path.basename(file_path)} [编码: {used_encoding}]"
                )
                continue

            # 获取前4列数据（不管列名是什么）
            num_columns = min(4, len(df.columns))  # 取实际列数和4的最小值

            if num_columns == 0:
                print(
                    f"○ 跳过无列数据的文件: {os.path.basename(file_path)} [编码: {used_encoding}]"
                )
                continue

            # 提取前num_columns列
            df_selected = df.iloc[:, :num_columns].copy()

            # 重命名列为A、B、C、D（根据实际列数）
            column_names = ["A", "B", "C", "D"][:num_columns]
            df_selected.columns = column_names

            # 如果列数不足4列，补充空列
            for j in range(num_columns, 4):
                df_selected[column_names[j]] = ""

            # 添加文件来源列
            df_selected["文件来源"] = os.path.basename(file_path)

            # 删除所有ABCD列都为空的行
            df_selected_clean = df_selected.copy()
            # 检查ABCD列是否全为空（包括NaN、空字符串、只有空格的情况）
            abcd_columns = ["A", "B", "C", "D"]
            for col in abcd_columns:
                if col in df_selected_clean.columns:
                    df_selected_clean[col] = (
                        df_selected_clean[col].astype(str).str.strip()
                    )
                    df_selected_clean[col] = df_selected_clean[col].replace("nan", "")

            # 保留至少有一个ABCD列不为空的行
            mask = df_selected_clean[abcd_columns].apply(
                lambda x: x.str.len().sum() > 0, axis=1
            )
            df_selected_final = df_selected[mask].copy()

            if not df_selected_final.empty:
                all_data.append(df_selected_final)
                print(
                    f"✓ 已处理文件 {i}/{len(csv_files)}: {os.path.basename(file_path)} ({len(df_selected_final)} 行, {num_columns} 列) [编码: {used_encoding}]"
                )
            else:
                print(
                    f"○ 跳过空数据文件: {os.path.basename(file_path)} [编码: {used_encoding}]"
                )

        except Exception as e:
            print(f"✗ 处理文件 '{os.path.basename(file_path)}' 时发生错误：{e}")

    # 检查是否有数据要合并
    if not all_data:
        print("错误：没有找到可以合并的数据！")
        return

    # 合并所有数据
    try:
        merged_df = pd.concat(all_data, ignore_index=True)

        # 确保列的顺序：A、B、C、D、文件来源
        column_order = ["A", "B", "C", "D", "文件来源"]
        merged_df = merged_df[column_order]

        # 输出Excel文件名
        output_file = "合并后的ABCD列数据.xlsx"

        # 保存为Excel文件
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            merged_df.to_excel(writer, sheet_name="合并数据", index=False)

        print(f"\n✅ 成功！")
        print(f"📁 已将 {len(all_data)} 个文件的数据合并")
        print(f"📊 合并后共有 {len(merged_df)} 行数据")
        print(f"💾 输出文件：{output_file}")

        # 显示合并后的数据预览
        print(f"\n📋 数据预览（前5行）：")
        print(merged_df.head())

        # 显示每个文件的数据统计
        print(f"\n📈 各文件数据统计：")
        file_counts = merged_df["文件来源"].value_counts()
        for filename, count in file_counts.items():
            print(f"  {filename}: {count} 行")

        # 显示数据总览
        print(f"\n📋 数据概况：")
        print(f"  总行数: {len(merged_df)}")
        print(
            f"  A列非空: {merged_df['A'].astype(str).str.strip().replace('', pd.NA).notna().sum()}"
        )
        print(
            f"  B列非空: {merged_df['B'].astype(str).str.strip().replace('', pd.NA).notna().sum()}"
        )
        print(
            f"  C列非空: {merged_df['C'].astype(str).str.strip().replace('', pd.NA).notna().sum()}"
        )
        print(
            f"  D列非空: {merged_df['D'].astype(str).str.strip().replace('', pd.NA).notna().sum()}"
        )

    except Exception as e:
        print(f"✗ 保存文件时发生错误：{e}")
        print("提示：请确保安装了 openpyxl 库：pip install openpyxl")


def main():
    """
    主函数
    """
    print("🔄 开始拼接CSV文件的前4列数据到Excel...")
    print("-" * 60)

    # 检查是否安装了openpyxl
    try:
        import openpyxl
    except ImportError:
        print("⚠️ 缺少依赖库！请先安装：")
        print("pip install openpyxl")
        return

    concat_csv_first_four_columns()

    print("-" * 60)
    print("🏁 脚本执行完成！")


if __name__ == "__main__":
    main()
