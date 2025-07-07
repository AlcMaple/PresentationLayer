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
        self.excel_file = Path(excel_file)
        if not self.excel_file.exists():
            raise FileNotFoundError(f"Excel文件不存在: {excel_file}")

        self.output_dir = (
            Path(output_dir) if output_dir else self.excel_file.parent / "json_output"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "total_sheets": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "errors": [],
        }

    def get_sheet_names(self) -> List[str]:
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
        try:
            df_raw = pd.read_excel(self.excel_file, sheet_name=sheet_name, header=None)

            if orient == "hierarchical" or hierarchical:
                return self._convert_to_hierarchical_json(df_raw, sheet_name)

            if header_row is not None:
                df = pd.read_excel(
                    self.excel_file, sheet_name=sheet_name, header=header_row
                )
            else:
                df = pd.read_excel(self.excel_file, sheet_name=sheet_name)

            if handle_nan == "null":
                df = df.where(pd.notnull(df), None)
            elif handle_nan == "drop":
                df = df.dropna()
            elif handle_nan == "fill":
                df = df.fillna("")

            for col in df.columns:
                if df[col].dtype == "datetime64[ns]":
                    if date_format == "iso":
                        df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
                    elif date_format == "epoch":
                        df[col] = df[col].astype(int) // 10**9

            if orient == "records":
                return df.to_dict(orient="records")
            elif orient == "index":
                return df.to_dict(orient="index")
            elif orient == "values":
                return {"columns": df.columns.tolist(), "data": df.values.tolist()}
            elif orient == "table":
                return df.to_dict(orient="table")
            else:
                return df.to_dict(orient="records")

        except Exception as e:
            error_msg = f"转换工作表 '{sheet_name}' 失败: {e}"
            print(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return None

    def _convert_to_hierarchical_json(
        self, df_raw: pd.DataFrame, sheet_name: str = None
    ) -> Dict:
        try:
            json_result = {}
            parents = []

            for idx, row in df_raw.iterrows():
                if row.isnull().all():
                    continue  # 跳过空行

                clean_row = [
                    str(item).strip() if pd.notnull(item) else "" for item in row
                ]
                levels = [cell for cell in clean_row if cell != ""]

                if not levels:
                    continue  # 跳过全空行

                # 层级结构解析：假设每一列代表一个层级
                for col_index, cell in enumerate(row):
                    if pd.notnull(cell):
                        current_level = str(cell).strip()
                        if len(parents) > col_index:
                            parents[col_index] = current_level
                        else:
                            parents.append(current_level)
                        parents = parents[: col_index + 1]

                        # 插入节点
                        pointer = json_result
                        for level in parents[:-1]:
                            pointer = pointer.setdefault(level, {})

                        pointer.setdefault(current_level, {})

            return json_result

        except Exception as e:
            error_msg = f"层级结构转换失败（工作表: {sheet_name}）: {e}"
            print(f"❌ {error_msg}")
            self.stats["errors"].append(error_msg)
            return None

    def save_json_file(
        self, data: Dict, filename: str, indent: int = 2, ensure_ascii: bool = False
    ) -> bool:
        try:
            output_file = self.output_dir / f"{filename}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    data, f, indent=indent, ensure_ascii=ensure_ascii, default=str
                )

            print(f"✅ 保存成功: {output_file} ({output_file.stat().st_size:,} bytes)")
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
        print(f"🚀 开始转换 Excel 文件: {self.excel_file}")
        print(f"📁 输出目录: {self.output_dir}")
        print("-" * 50)

        sheet_names = self.get_sheet_names()
        if not sheet_names:
            print("❌ 未找到任何工作表")
            return self.stats

        self.stats["total_sheets"] = len(sheet_names)
        print(f"📋 发现 {len(sheet_names)} 个工作表: {', '.join(sheet_names)}")
        print("-" * 50)

        for i, sheet_name in enumerate(sheet_names, 1):
            print(f"\n[{i}/{len(sheet_names)}] 处理工作表: {sheet_name}")
            json_data = self.convert_sheet_to_json(
                sheet_name, orient, handle_nan, date_format, hierarchical
            )

            if json_data is not None:
                clean_name = "".join(
                    c for c in sheet_name if c.isalnum() or c in (" ", "-", "_")
                ).strip()
                filename = f"{filename_prefix}{clean_name}{filename_suffix}"
                if self.save_json_file(json_data, filename):
                    self.stats["successful_conversions"] += 1
                else:
                    self.stats["failed_conversions"] += 1
            else:
                self.stats["failed_conversions"] += 1

        self.print_summary()
        return self.stats

    def print_summary(self):
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
    parser = argparse.ArgumentParser(
        description="将Excel文件的每个工作表转换为单独的JSON文件"
    )

    parser.add_argument("excel_file", help="Excel文件路径")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument(
        "--orient",
        choices=["records", "index", "values", "table", "hierarchical"],
        default="records",
        help="输出JSON的格式",
    )
    parser.add_argument(
        "--handle_nan",
        choices=["null", "drop", "fill"],
        default="null",
        help="如何处理NaN值",
    )
    parser.add_argument(
        "--date_format", choices=["iso", "epoch"], default="iso", help="日期格式"
    )
    parser.add_argument("--prefix", default="", help="输出文件名前缀")
    parser.add_argument("--suffix", default="", help="输出文件名后缀")
    parser.add_argument(
        "--hierarchical", action="store_true", help="是否使用层级结构格式"
    )

    args = parser.parse_args()

    converter = ExcelToJsonConverter(args.excel_file, args.output)
    converter.convert_all_sheets(
        orient=args.orient,
        handle_nan=args.handle_nan,
        date_format=args.date_format,
        filename_prefix=args.prefix,
        filename_suffix=args.suffix,
        hierarchical=args.hierarchical,
    )


if __name__ == "__main__":
    main()
