import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlmodel import Session
from services.bridge_query import get_bridge_query_service


def test_basic_query():
    """测试基本查询功能"""
    print("=" * 60)
    print("测试基本查询功能")
    print("=" * 60)

    with Session(engine) as session:
        query_service = get_bridge_query_service(session)

        # 获取总数
        total_count = query_service.count_total_paths()
        print(f"路径总数: {total_count}")

        # 获取前5条记录
        paths = query_service.get_paths_with_names(limit=5, offset=0)

        print(f"\n前5条路径记录:")
        print("-" * 60)

        for i, path in enumerate(paths, 1):
            print(f"记录 {i} (ID: {path.id}):")
            print(f"  分类: {path.category_name} (code: {path.category_code})")
            print(
                f"  评定单元: {path.assessment_unit_name} (code: {path.assessment_unit_code})"
            )
            print(
                f"  桥梁类型: {path.bridge_type_name} (code: {path.bridge_type_code})"
            )
            print(f"  部位: {path.part_name} (code: {path.part_code})")
            print(f"  结构类型: {path.structure_name} (code: {path.structure_code})")
            print(
                f"  部件类型: {path.component_type_name} (code: {path.component_type_code})"
            )
            print(
                f"  构件形式: {path.component_form_name} (code: {path.component_form_code})"
            )
            print(f"  病害类型: {path.disease_name} (code: {path.disease_code})")
            print(f"  标度: {path.scale_name} (code: {path.scale_code})")
            print(f"  定性描述: {path.quality_name} (code: {path.quality_code})")
            print(f"  定量描述: {path.quantity_name} (code: {path.quantity_code})")
            print("-" * 40)


def test_disease_search():
    """测试病害类型搜索"""
    print("\n" + "=" * 60)
    print("测试病害类型搜索功能")
    print("=" * 60)

    with Session(engine) as session:
        query_service = get_bridge_query_service(session)

        # 搜索"蜂窝"病害
        disease_name = "蜂窝"
        paths = query_service.search_by_disease(disease_name)

        print(f"搜索病害类型 '{disease_name}' 的结果:")
        print(f"找到 {len(paths)} 条记录")
        print("-" * 60)

        # 统计桥梁类型分布
        bridge_type_stats = {}
        for path in paths:
            bridge_type = path.bridge_type_name or "未知"
            bridge_type_stats[bridge_type] = bridge_type_stats.get(bridge_type, 0) + 1

        print("按桥梁类型分组统计:")
        for bridge_type, count in bridge_type_stats.items():
            print(f"  {bridge_type}: {count} 条")

        # 显示前3条详细记录
        print(f"\n前3条详细记录:")
        for i, path in enumerate(paths[:3], 1):
            print(f"记录 {i}:")
            print(f"  分类: {path.category_name} (code: {path.category_code})")
            print(
                f"  评定单元: {path.assessment_unit_name} (code: {path.assessment_unit_code})"
            )
            print(
                f"  桥梁类型: {path.bridge_type_name} (code: {path.bridge_type_code})"
            )
            print(f"  部位: {path.part_name} (code: {path.part_code})")
            print(f"  病害类型: {path.disease_name} (code: {path.disease_code})")
            print(f"  标度: {path.scale_name} (code: {path.scale_code})")
            print(f"  定性描述: {path.quality_name} (code: {path.quality_code})")
            print("-" * 30)


def test_pagination():
    """测试分页功能"""
    print("\n" + "=" * 60)
    print("测试分页功能")
    print("=" * 60)

    with Session(engine) as session:
        query_service = get_bridge_query_service(session)

        # 测试第1页
        page1 = query_service.get_paths_with_names(limit=3, offset=0)
        print("第1页 (前3条):")
        for i, path in enumerate(page1, 1):
            print(
                f"  {i}. {path.category_name} -> {path.bridge_type_name}({path.bridge_type_code}) -> {path.disease_name}({path.disease_code})"
            )

        # 测试第2页
        page2 = query_service.get_paths_with_names(limit=3, offset=3)
        print("\n第2页 (第4-6条):")
        for i, path in enumerate(page2, 1):
            print(
                f"  {i+3}. {path.category_name} -> {path.bridge_type_name}({path.bridge_type_code}) -> {path.disease_name}({path.disease_code})"
            )


def test_hierarchy_display():
    """测试11层结构层级显示"""
    print("\n" + "=" * 60)
    print("测试11层结构层级显示")
    print("=" * 60)

    with Session(engine) as session:
        query_service = get_bridge_query_service(session)

        # 获取前3条记录展示完整层级
        paths = query_service.get_paths_with_names(limit=3, offset=0)

        for i, path in enumerate(paths, 1):
            print(f"\n【路径 {i}】完整11层结构:")
            print(f"  1. 分类: {path.category_name}")
            print(f"  2. 评定单元: {path.assessment_unit_name}")
            print(f"  3. 桥梁类型: {path.bridge_type_name}")
            print(f"  4. 部位: {path.part_name}")
            print(f"  5. 结构类型: {path.structure_name}")
            print(f"  6. 部件类型: {path.component_type_name}")
            print(f"  7. 构件形式: {path.component_form_name}")
            print(f"  8. 病害类型: {path.disease_name}")
            print(f"  9. 标度: {path.scale_name}")
            print(f"  10. 定性描述: {path.quality_name}")
            print(f"  11. 定量描述: {path.quantity_name}")
            print("-" * 50)


def main():
    """主测试函数"""
    try:
        test_basic_query()
        test_disease_search()
        test_pagination()
        test_hierarchy_display()

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
