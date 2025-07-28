import json
import sys
import os
from typing import Dict, Any
from decimal import Decimal

from sqlmodel import Session, select

# 添加项目根目录到路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from models import (
    WeightReferences,
    BridgeTypes,
    BridgeParts,
    BridgeStructures,
    BridgeComponentTypes,
)


class WeightDataImporter:
    """
    从JSON文件导入桥梁权重参考数据到数据库。
    """

    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.session = Session(engine)
        print("数据库会话已创建。")

        # 用于存储从数据库加载的 name -> id 映射
        self.bridge_type_map: Dict[str, int] = {}
        self.part_map: Dict[str, int] = {}
        self.structure_map: Dict[str, int] = {}
        self.component_type_map: Dict[str, int] = {}
        self.records_to_add: list = []

    def _load_json_data(self) -> Dict:
        """加载并返回JSON数据"""
        print(f"正在加载JSON文件: {self.json_file_path}")
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("✅ JSON文件加载成功。")
            return data
        except FileNotFoundError:
            print(f"❌ 错误: JSON文件未找到 at '{self.json_file_path}'")
            raise
        except json.JSONDecodeError as e:
            print(f"❌ 错误: JSON文件格式无效: {e}")
            raise

    def _load_name_to_id_maps(self):
        """从数据库加载基础数据，构建名称到ID的映射字典"""
        print("正在从数据库加载名称到ID的映射...")
        try:
            self.bridge_type_map = {
                bt.name: bt.id for bt in self.session.exec(select(BridgeTypes)).all()
            }
            self.part_map = {
                p.name: p.id for p in self.session.exec(select(BridgeParts)).all()
            }
            self.structure_map = {
                s.name: s.id for s in self.session.exec(select(BridgeStructures)).all()
            }
            self.component_type_map = {
                ct.name: ct.id
                for ct in self.session.exec(select(BridgeComponentTypes)).all()
            }
            print("✅ 名称映射加载完成。")
            print(f"  - 桥梁类型: {len(self.bridge_type_map)}条")
            print(f"  - 部位: {len(self.part_map)}条")
            print(f"  - 结构类型: {len(self.structure_map)}条")
            print(f"  - 部件类型: {len(self.component_type_map)}条")
        except Exception as e:
            print(f"❌ 加载名称映射时出错: {e}")
            raise

    def _recursive_import(self, current_node: Dict, parent_ids: Dict[str, int]):
        """
        递归遍历JSON节点，收集ID并创建WeightReferences记录。

        Args:
            current_node (Dict): 当前正在处理的JSON节点 (children字典).
            parent_ids (Dict[str, int]): 从上层继承的ID路径.
        """
        for name, child_node in current_node.items():
            level = child_node.get("level")
            current_ids = parent_ids.copy()

            # 根据层级，查找ID并更新路径
            if level == "部位":
                part_id = self.part_map.get(name)
                if part_id is None:
                    print(f"⚠️ 警告: 找不到部位 '{name}' 的ID，跳过其下所有权重。")
                    continue
                current_ids["part_id"] = part_id

            elif level == "结构类型":
                structure_id = self.structure_map.get(name)
                if structure_id is None:
                    print(f"⚠️ 警告: 找不到结构类型 '{name}' 的ID，跳过其下所有权重。")
                    continue
                current_ids["structure_id"] = structure_id

            # 检查是否到达终点（包含权重的节点）
            if "weight" in child_node:
                component_id = self.component_type_map.get(name)
                if component_id is None:
                    print(f"⚠️ 警告: 找不到部件类型 '{name}' 的ID，无法保存此权重。")
                    continue
                current_ids["component_type_id"] = component_id

                # 创建WeightReferences对象
                weight_record = WeightReferences(
                    bridge_type_id=current_ids["bridge_type_id"],
                    part_id=current_ids["part_id"],
                    structure_id=current_ids.get("structure_id"),  # 可能不存在
                    component_type_id=current_ids["component_type_id"],
                    # 使用Decimal转换，并先转为字符串以避免浮点数精度问题
                    weight=Decimal(str(child_node["weight"])),
                    is_active=True,
                    remarks=f"Imported from {os.path.basename(self.json_file_path)}",
                )
                self.records_to_add.append(weight_record)

            # 如果还有子节点，则继续递归
            elif "children" in child_node:
                self._recursive_import(child_node["children"], current_ids)

    def run_import(self):
        """执行完整的导入流程"""
        try:
            # 1. 加载JSON数据
            data = self._load_json_data()

            # 2. 加载名称到ID的映射
            self._load_name_to_id_maps()

            # 3. 遍历JSON并准备要插入的数据
            print("🚀 开始解析JSON数据并准备数据库记录...")
            bridge_types_data = data.get("bridge_types", {})
            for bt_name, bt_data in bridge_types_data.items():
                bridge_type_id = self.bridge_type_map.get(bt_name)
                if bridge_type_id is None:
                    print(
                        f"⚠️ 警告: 找不到桥梁类型 '{bt_name}' 的ID，跳过此类型下所有权重。"
                    )
                    continue

                print(f"  -> 正在处理: {bt_name}")
                # 从"桥梁类型"的子节点开始递归
                self._recursive_import(
                    bt_data.get("children", {}), {"bridge_type_id": bridge_type_id}
                )

            # 4. 批量插入数据
            if not self.records_to_add:
                print("🔵 没有找到可导入的新权重记录。")
                return

            print(f"准备将 {len(self.records_to_add)} 条权重记录插入数据库...")

            # 在插入前，可以选择性地删除旧数据
            # print("正在删除旧的权重参考数据...")
            # self.session.query(WeightReferences).delete()

            self.session.add_all(self.records_to_add)
            self.session.commit()

            print(f"✅ 成功！{len(self.records_to_add)} 条权重记录已导入数据库。")

        except Exception as e:
            print(f"❌ 导入过程中发生严重错误: {e}")
            print("正在回滚事务...")
            self.session.rollback()
            raise
        finally:
            print("关闭数据库会话。")
            self.session.close()


def main():
    """主函数"""
    print("--- 权重参考数据导入脚本 ---")

    # JSON文件路径
    json_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "static",
        "json_output",
        "weights.json",
    )

    if not os.path.exists(json_file):
        print(f"❌ 错误: JSON文件不存在于 '{json_file}'")
        print("请先运行 'convert_weights_to_json.py' 脚本生成该文件。")
        return

    # 执行导入
    importer = WeightDataImporter(json_file)
    importer.run_import()


if __name__ == "__main__":
    main()
