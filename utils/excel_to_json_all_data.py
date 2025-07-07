#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel转JSON工具
将Excel文件中的每个工作表转换为单独的JSON文件

依赖库：
pip install pandas openpyxl xlrd
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from datetime import datetime


class ExcelToJsonConverter:
    """Excel转JSON转换器"""

    def __init__(self, excel_file: str, output_dir: str = None):
        """
        初始化转换器

        Args:
            excel_file: Excel文件路径
            output_dir: 输出目录，默认为Excel文件同级目录下的json文件夹
        """
        self.excel_file = Path(excel_file)
        if not self.excel_file.exists():
            raise FileNotFoundError(f"Excel文件不存在: {excel_file}")

        # 设置输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.excel_file.parent / "json_output"

        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)

        # 记录转换统计
        self.stats = {
            "total_sheets": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "errors": [],
        }

    def get_sheet_names(self) -> List[str]:
        """获取Excel文件中的所有工作表名称"""
        try:
            with pd.ExcelFile(self.excel_file) as xls:
                return xls.sheet_names
        except Exception as e:
            print(f"❌ 读取Excel文件失败: {e}")
            return []

    def convert_sheet_to_json(
        self,
        sheet_name: str,
        orient: str = "records",
        handle_nan: str = "null",
        date_format: str = "iso",
        hierarchical: bool = False,
        header_row: int = None,
    ) -> Optional[Dict]:
        """
        将单个工作表转换为JSON数据

        Args:
            sheet_name: 工作表名称
            orient: JSON格式 ('records', 'index', 'values', 'table', 'hierarchical')
            handle_nan: NaN值处理方式 ('null', 'drop', 'fill')
            date_format: 日期格式 ('iso', 'epoch')
            hierarchical: 是否处理层级结构
            header_row: 指定列标题所在行号（0开始），None表示自动检测

        Returns:
            转换后的JSON数据
        """
        try:
            # 先读取原始数据（不指定header）
            df_raw = pd.read_excel(self.excel_file, sheet_name=sheet_name, header=None)

            print(f"📊 处理工作表: {sheet_name} (原始形状: {df_raw.shape})")
            print("🔍 原始前几行数据预览:")
            for i in range(min(5, len(df_raw))):
                row_data = [str(x) if not pd.isna(x) else "NaN" for x in df_raw.iloc[i]]
                print(f"  第{i+1}行: {row_data}")

            # 如果是层级结构格式，使用原始数据进行处理
            if orient == "hierarchical" or hierarchical:
                return self._convert_to_hierarchical_json(df_raw, sheet_name)

            # 对于其他格式，使用标准处理
            if header_row is not None:
                df = pd.read_excel(
                    self.excel_file, sheet_name=sheet_name, header=header_row
                )
            else:
                df = pd.read_excel(self.excel_file, sheet_name=sheet_name)

            # 处理NaN值
            if handle_nan == "null":
                df = df.where(pd.notnull(df), None)
            elif handle_nan == "drop":
                df = df.dropna()
            elif handle_nan == "fill":
                df = df.fillna("")

            # 处理日期列
            for col in df.columns:
                if df[col].dtype == "datetime64[ns]":
                    if date_format == "iso":
                        df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
                    elif date_format == "epoch":
                        df[col] = df[col].astype(int) // 10**9

            # 转换为JSON格式
            if orient == "records":
                json_data = df.to_dict(orient="records")
            elif orient == "index":
                json_data = df.to_dict(orient="index")
            elif orient == "values":
                json_data = {"columns": df.columns.tolist(), "data": df.values.tolist()}
            elif orient == "table":
                json_data = df.to_dict(orient="table")
            else:
                json_data = df.to_dict(orient="records")

            return json_data

        except Exception as e:
            error_msg = f"转换工作表 '{sheet_name}' 失败: {e}"
            print(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return None

    def _convert_to_hierarchical_json(
        self, df_raw: pd.DataFrame, sheet_name: str = None
    ) -> Dict:
        """
        将DataFrame转换为层级JSON结构
        专门处理带有合并单元格的分层表格
        """
        print(f"📊 原始DataFrame形状: {df_raw.shape}")

        # 智能识别标题
        title = sheet_name or "数据表"  # 优先使用工作表名称作为标题

        # 尝试在前几行中寻找更好的标题
        for row_idx in range(min(3, len(df_raw))):
            row = df_raw.iloc[row_idx]
            for val in row:
                if not pd.isna(val) and str(val).strip():
                    potential_title = str(val).strip()
                    # 如果找到包含关键词的更长标题，使用它
                    if any(
                        keyword in potential_title
                        for keyword in [
                            "桥梁",
                            "部件",
                            "公路",
                            "各类",
                            "分类",
                            "构件",
                            "病害",
                        ]
                    ) and len(potential_title) > len(
                        title if title != sheet_name else ""
                    ):
                        title = potential_title
                        print(f"✅ 在第{row_idx+1}行发现更好的标题: {title}")
                        break

        # 智能识别列标题行
        headers = []
        data_start_row = 0
        total_columns = len(df_raw.columns)

        for row_idx in range(min(4, len(df_raw))):
            row = df_raw.iloc[row_idx]
            non_empty_vals = [
                str(val).strip() for val in row if not pd.isna(val) and str(val).strip()
            ]

            # 检查这一行是否像列标题
            if len(non_empty_vals) >= 3:  # 至少3个非空值
                header_keywords = [
                    "类型",
                    "部位",
                    "类别",
                    "评价",
                    "名称",
                    "桥梁",
                    "结构",
                    "部件",
                    "构件",
                    "病害",
                ]
                if any(
                    any(keyword in header for keyword in header_keywords)
                    for header in non_empty_vals
                ):
                    # 构建完整的headers数组
                    headers = []
                    for i in range(total_columns):
                        if i < len(row):
                            val = row.iloc[i]
                            if not pd.isna(val) and str(val).strip():
                                headers.append(str(val).strip())
                            else:
                                headers.append(f"列{i+1}")
                        else:
                            headers.append(f"列{i+1}")

                    data_start_row = row_idx + 1
                    print(f"✅ 在第{row_idx+1}行发现列标题: {headers}")
                    break

        # 如果没找到列标题，使用第一行作为列标题
        if not headers:
            headers = [f"列{i+1}" for i in range(total_columns)]
            data_start_row = 1
            print(f"🔄 使用默认列标题: {headers}")

        print(f"📋 最终标题: {title}")
        print(f"📋 最终列标题: {headers}")
        print(f"📋 总列数: {total_columns}")
        print(f"📋 数据开始行: 第{data_start_row+1}行")

        # 构建层级数据结构
        hierarchical_data = {}
        current_type = None
        current_location = None

        # 从确定的数据开始行处理数据
        for idx in range(data_start_row, len(df_raw)):
            row = df_raw.iloc[idx]

            # 获取所有列的值
            values = []
            for i in range(total_columns):
                if i < len(row):
                    val = row.iloc[i]
                    if pd.isna(val):
                        values.append(None)
                    else:
                        values.append(str(val).strip() if str(val).strip() else None)
                else:
                    values.append(None)

            # 跳过完全空白的行
            if all(val is None or val == "" for val in values):
                continue

            print(f"🔍 第{idx+1}行数据: {values}")

            # 前两列通常是桥梁类型和部位
            bridge_type_val = values[0] if len(values) > 0 else None
            location_val = values[1] if len(values) > 1 else None

            # 更新当前类型
            if bridge_type_val and bridge_type_val not in ["NaN", ""]:
                current_type = bridge_type_val
                if current_type not in hierarchical_data:
                    hierarchical_data[current_type] = {}
                    print(f"🏗️  新建桥梁类型: {current_type}")

            # 更新当前部位
            if location_val and location_val not in ["NaN", ""]:
                current_location = location_val
                if (
                    current_type
                    and current_location not in hierarchical_data[current_type]
                ):
                    hierarchical_data[current_type][current_location] = []
                    print(f"   新建部位: {current_location}")

            # 添加具体数据 - 从第3列开始的所有数据
            if current_type and current_location:
                # 检查是否有有效的数据列（从第3列开始）
                data_columns = values[2:] if len(values) > 2 else []
                if any(val is not None and val != "" for val in data_columns):
                    item = {}

                    # 动态添加所有数据列
                    for i, val in enumerate(data_columns):
                        header_index = i + 2  # 对应headers的索引
                        if header_index < len(headers):
                            header_name = headers[header_index]

                            # 处理特殊值
                            if val is None or val == "":
                                processed_val = None
                            elif val == "/":
                                processed_val = "/"
                            else:
                                # 尝试转换数字
                                try:
                                    if "." in val:
                                        processed_val = float(val)
                                    else:
                                        processed_val = int(val)
                                except (ValueError, TypeError):
                                    processed_val = val

                            item[header_name] = processed_val

                    # 只有当item不为空时才添加
                    if item:
                        hierarchical_data[current_type][current_location].append(item)
                        print(f"     添加部件: {item}")

        # 构建最终JSON结构
        result = {
            "title": title,
            "headers": headers,
            "data": hierarchical_data,
            "metadata": {
                "total_types": len(hierarchical_data),
                "total_columns": total_columns,
                "conversion_time": datetime.now().isoformat(),
                "source_sheet": sheet_name or "hierarchical_structure",
                "data_start_row": data_start_row + 1,
            },
        }

        return result

    def save_json_file(
        self, data: Dict, filename: str, indent: int = 2, ensure_ascii: bool = False
    ) -> bool:
        """
        保存JSON数据到文件

        Args:
            data: JSON数据
            filename: 文件名
            indent: 缩进空格数
            ensure_ascii: 是否确保ASCII编码

        Returns:
            是否保存成功
        """
        try:
            output_file = self.output_dir / f"{filename}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    data, f, indent=indent, ensure_ascii=ensure_ascii, default=str
                )  # default=str 处理无法序列化的对象

            file_size = output_file.stat().st_size
            print(f"✅ 保存成功: {output_file} ({file_size:,} bytes)")
            return True

        except Exception as e:
            error_msg = f"保存文件 '{filename}.json' 失败: {e}"
            print(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return False

    def convert_all_sheets(
        self,
        orient: str = "records",
        handle_nan: str = "null",
        date_format: str = "iso",
        filename_prefix: str = "",
        filename_suffix: str = "",
        hierarchical: bool = False,
    ) -> Dict:
        """
        转换所有工作表

        Args:
            orient: JSON格式
            handle_nan: NaN值处理方式
            date_format: 日期格式
            filename_prefix: 文件名前缀
            filename_suffix: 文件名后缀
            hierarchical: 是否使用层级结构格式

        Returns:
            转换统计信息
        """
        print(f"🚀 开始转换 Excel 文件: {self.excel_file}")
        print(f"📁 输出目录: {self.output_dir}")
        print("-" * 50)

        # 获取所有工作表
        sheet_names = self.get_sheet_names()
        if not sheet_names:
            print("❌ 未找到任何工作表")
            return self.stats

        self.stats["total_sheets"] = len(sheet_names)
        print(f"📋 发现 {len(sheet_names)} 个工作表: {', '.join(sheet_names)}")
        print("-" * 50)

        # 逐个转换工作表
        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"\n[{i}/{len(sheet_names)}] 处理工作表: {sheet_name}")

            # 转换为JSON
            json_data = self.convert_sheet_to_json(
                sheet_name, orient, handle_nan, date_format, hierarchical
            )

            if json_data is not None:
                # 生成文件名（清理特殊字符）
                clean_name = "".join(
                    c for c in sheet_name if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                filename = f"{filename_prefix}{clean_name}{filename_suffix}"

                # 保存文件
                if self.save_json_file(json_data, filename):
                    self.stats["successful_conversions"] += 1
                else:
                    self.stats["failed_conversions"] += 1
            else:
                self.stats["failed_conversions"] += 1

        # 输出统计信息
        self.print_summary()
        return self.stats

    def print_summary(self):
        """打印转换摘要"""
        print("\n" + "=" * 50)
        print("📊 转换完成！统计信息:")
        print(f"   总工作表数: {self.stats['total_sheets']}")
        print(f"   ✅ 成功转换: {self.stats['successful_conversions']}")
        print(f"   ❌ 转换失败: {self.stats['failed_conversions']}")

        if self.stats["errors"]:
            print(f"\n❌ 错误详情:")
            for error in self.stats["errors"]:
                print(f"   - {error}")

        print(f"\n📁 输出目录: {self.output_dir}")
        print("=" * 50)


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description="将Excel文件的每个工作表转换为单独的JSON文件"
    )

    parser.add_argument("excel_file", help="Excel文件路径")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument(
        "--orient",
        choices=["records", "index", "values", "table", "hierarchical"],
        default="records",
        help="JSON格式 (默认: records)",
    )
    parser.add_argument(
        "--hierarchical",
        action="store_true",
        help="使用层级结构格式（适合合并单元格表格）",
    )
    parser.add_argument(
        "--nan",
        choices=["null", "drop", "fill"],
        default="null",
        help="NaN值处理 (默认: null)",
    )
    parser.add_argument(
        "--date-format",
        choices=["iso", "epoch"],
        default="iso",
        help="日期格式 (默认: iso)",
    )
    parser.add_argument("--prefix", default="", help="文件名前缀")
    parser.add_argument("--suffix", default="", help="文件名后缀")

    args = parser.parse_args()

    try:
        # 创建转换器
        converter = ExcelToJsonConverter(args.excel_file, args.output)

        # 执行转换
        stats = converter.convert_all_sheets(
            orient=args.orient,
            handle_nan=args.nan,
            date_format=args.date_format,
            filename_prefix=args.prefix,
            filename_suffix=args.suffix,
            hierarchical=args.hierarchical or args.orient == "hierarchical",
        )

        # 根据结果设置退出码
        if stats["failed_conversions"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        sys.exit(1)


# 使用示例
if __name__ == "__main__":
    # 如果作为脚本运行，执行命令行版本
    if len(sys.argv) > 1:
        main()
    else:
        # 交互式使用示例
        print("Excel转JSON工具 - 交互式模式")
        print("=" * 40)

        # 示例用法
        excel_file = input("请输入Excel文件路径: ").strip()
        if not excel_file:
            print("未提供文件路径，使用示例...")
            excel_file = "sample.xlsx"  # 替换为你的Excel文件

        try:
            converter = ExcelToJsonConverter(excel_file)

            print("\n选择转换选项:")
            print("1. 默认设置 (records格式，保留null值)")
            print("2. 层级结构格式 (适合你的桥梁部件表格)")
            print("3. 自定义设置")

            choice = input("请选择 (1/2/3): ").strip()

            if choice == "2":
                print("🏗️  使用层级结构格式转换...")
                converter.convert_all_sheets(orient="hierarchical", hierarchical=True)
            elif choice == "3":
                orient = (
                    input(
                        "JSON格式 (records/index/values/table/hierarchical) [records]: "
                    ).strip()
                    or "records"
                )
                hierarchical = input("使用层级结构？(y/n) [n]: ").strip().lower() == "y"
                handle_nan = (
                    input("NaN处理 (null/drop/fill) [null]: ").strip() or "null"
                )
                date_format = input("日期格式 (iso/epoch) [iso]: ").strip() or "iso"
                prefix = input("文件名前缀 [空]: ").strip()
                suffix = input("文件名后缀 [空]: ").strip()

                converter.convert_all_sheets(
                    orient, handle_nan, date_format, prefix, suffix, hierarchical
                )
            else:
                converter.convert_all_sheets()

        except Exception as e:
            print(f"❌ 错误: {e}")
