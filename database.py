from sqlmodel import SQLModel, create_engine, Session, select
from models import *
import os

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root:123qweQWE!@localhost:3306/bridge_demo"
)

# 创建引擎
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """创建数据库和表"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session


def init_demo_data():
    """初始化简化版演示数据"""
    with Session(engine) as session:
        # 检查是否已有数据
        existing_bridge_types = session.exec(select(BridgeType)).first()
        if existing_bridge_types:
            print("演示数据已存在，跳过初始化")
            return

        print("开始初始化简化版演示数据...")

        # 1. 创建桥类型
        bridge_types = [
            BridgeType(
                code="beam",
                name="梁式桥",
                description="以梁作为主要承重结构的桥梁",
                sort_order=1,
            ),
            BridgeType(
                code="arch",
                name="拱式桥",
                description="以拱作为主要承重结构的桥梁",
                sort_order=2,
            ),
        ]

        for bt in bridge_types:
            session.add(bt)
        session.commit()

        # 刷新获取ID
        for bt in bridge_types:
            session.refresh(bt)

        # 2. 创建部位（独立表，可复用）
        parts = [
            Part(
                code="upper_structure",
                name="上部结构",
                description="桥梁上部结构",
                sort_order=1,
            ),
            Part(
                code="lower_structure",
                name="下部结构",
                description="桥梁下部结构",
                sort_order=2,
            ),
            Part(
                code="deck_system",
                name="桥面系",
                description="桥梁桥面系",
                sort_order=3,
            ),
            Part(
                code="main_arch",
                name="主拱圈",
                description="拱式桥主拱圈",
                sort_order=4,
            ),
        ]

        for part in parts:
            session.add(part)
        session.commit()

        # 刷新获取ID
        for part in parts:
            session.refresh(part)

        # 3. 创建结构类型
        structure_types = [
            # 上部结构的结构类型
            StructureType(
                code="steel_structure_a",
                name="钢结构A",
                description="钢结构类型A",
                part_id=parts[0].id,
                sort_order=1,
            ),
            StructureType(
                code="steel_structure_b",
                name="钢结构B",
                description="钢结构类型B",
                part_id=parts[0].id,
                sort_order=2,
            ),
            StructureType(
                code="concrete_structure",
                name="混凝土结构",
                description="混凝土结构",
                part_id=parts[1].id,
                sort_order=1,
            ),
            # 主拱圈的结构类型
            StructureType(
                code="arch_structure_c",
                name="拱结构C",
                description="拱结构类型C",
                part_id=parts[3].id,
                sort_order=1,
            ),
        ]

        for st in structure_types:
            session.add(st)
        session.commit()

        # 刷新获取ID
        for st in structure_types:
            session.refresh(st)

        # 4. 创建部件类型
        component_types = [
            # 钢结构A的部件类型
            ComponentType(
                code="main_beam_a",
                name="主梁A",
                description="主梁类型A",
                structure_type_id=structure_types[0].id,
                sort_order=1,
            ),
            # 钢结构B的部件类型
            ComponentType(
                code="main_beam_b",
                name="主梁B",
                description="主梁类型B",
                structure_type_id=structure_types[1].id,
                sort_order=1,
            ),
            # 混凝土结构的部件类型
            ComponentType(
                code="pier_body",
                name="墩身",
                description="混凝土墩身",
                structure_type_id=structure_types[2].id,
                sort_order=1,
            ),
            # 拱结构C的部件类型
            ComponentType(
                code="arch_ring_c",
                name="拱圈C",
                description="拱圈类型C",
                structure_type_id=structure_types[3].id,
                sort_order=1,
            ),
        ]

        for ct in component_types:
            session.add(ct)
        session.commit()

        # 刷新获取ID
        for ct in component_types:
            session.refresh(ct)

        # 5. 创建病害类型（独立表，可复用）
        damage_types = [
            DamageType(code="crack", name="裂缝", description="结构裂缝", sort_order=1),
            DamageType(
                code="corrosion", name="腐蚀", description="钢筋腐蚀", sort_order=2
            ),
            DamageType(
                code="settlement", name="沉降", description="结构沉降", sort_order=3
            ),
        ]

        for dt in damage_types:
            session.add(dt)
        session.commit()

        # 刷新获取ID
        for dt in damage_types:
            session.refresh(dt)

        # 6. 创建标度（包含完性描述和定量描述）
        scales = [
            Scale(
                code="level_1",
                name="1级",
                scale_value="1",
                qualitative_description="轻微缺陷，不影响使用",
                quantitative_description="裂缝宽度<0.1mm",
                sort_order=1,
            ),
            Scale(
                code="level_2",
                name="2级",
                scale_value="2",
                qualitative_description="一般缺陷，需要关注",
                quantitative_description="裂缝宽度0.1-0.2mm",
                sort_order=2,
            ),
            Scale(
                code="level_3",
                name="3级",
                scale_value="3",
                qualitative_description="明显缺陷，需要维修",
                quantitative_description="裂缝宽度0.2-0.5mm",
                sort_order=3,
            ),
            Scale(
                code="level_4",
                name="4级",
                scale_value="4",
                qualitative_description="严重缺陷，影响安全",
                quantitative_description="裂缝宽度0.5-1.0mm",
                sort_order=4,
            ),
            Scale(
                code="level_5",
                name="5级",
                scale_value="5",
                qualitative_description="极度危险，需要立即处理",
                quantitative_description="裂缝宽度>1.0mm",
                sort_order=5,
            ),
        ]

        for scale in scales:
            session.add(scale)
        session.commit()

        # 刷新获取ID
        for scale in scales:
            session.refresh(scale)

        # 7. 创建完整路径记录（核心功能）
        # 实现你提到的三个场景：
        # - 梁式桥 → 上部结构 → 钢结构A → 主梁A → 裂缝 → 标度1-3
        # - 梁式桥 → 上部结构 → 钢结构B → 主梁B → 裂缝 → 标度1-4
        # - 拱式桥 → 主拱圈 → 拱结构C → 拱圈C → 裂缝 → 标度1-5

        paths = [
            # 场景1：梁式桥 → 上部结构 → 钢结构A → 主梁A → 裂缝 → 标度1-3
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[0].id,
                structure_type_id=structure_types[0].id,
                component_type_id=component_types[0].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[0].id,
                sort_order=1,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[0].id,
                structure_type_id=structure_types[0].id,
                component_type_id=component_types[0].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[1].id,
                sort_order=2,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[0].id,
                structure_type_id=structure_types[0].id,
                component_type_id=component_types[0].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[2].id,
                sort_order=3,
            ),
            # 场景2：梁式桥 → 上部结构 → 钢结构B → 主梁B → 裂缝 → 标度1-4
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[0].id,
                structure_type_id=structure_types[1].id,
                component_type_id=component_types[1].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[0].id,
                sort_order=1,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[0].id,
                structure_type_id=structure_types[1].id,
                component_type_id=component_types[1].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[1].id,
                sort_order=2,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[0].id,
                structure_type_id=structure_types[1].id,
                component_type_id=component_types[1].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[2].id,
                sort_order=3,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[0].id,
                structure_type_id=structure_types[1].id,
                component_type_id=component_types[1].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[3].id,
                sort_order=4,
            ),
            # 场景3：拱式桥 → 主拱圈 → 拱结构C → 拱圈C → 裂缝 → 标度1-5
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[1].id,
                part_id=parts[3].id,
                structure_type_id=structure_types[3].id,
                component_type_id=component_types[3].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[0].id,
                sort_order=1,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[1].id,
                part_id=parts[3].id,
                structure_type_id=structure_types[3].id,
                component_type_id=component_types[3].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[1].id,
                sort_order=2,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[1].id,
                part_id=parts[3].id,
                structure_type_id=structure_types[3].id,
                component_type_id=component_types[3].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[2].id,
                sort_order=3,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[1].id,
                part_id=parts[3].id,
                structure_type_id=structure_types[3].id,
                component_type_id=component_types[3].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[3].id,
                sort_order=4,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[1].id,
                part_id=parts[3].id,
                structure_type_id=structure_types[3].id,
                component_type_id=component_types[3].id,
                damage_type_id=damage_types[0].id,
                scale_id=scales[4].id,
                sort_order=5,
            ),
            # 额外场景：梁式桥下部结构的腐蚀病害
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[1].id,
                structure_type_id=structure_types[2].id,
                component_type_id=component_types[2].id,
                damage_type_id=damage_types[1].id,
                scale_id=scales[0].id,
                sort_order=1,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[1].id,
                structure_type_id=structure_types[2].id,
                component_type_id=component_types[2].id,
                damage_type_id=damage_types[1].id,
                scale_id=scales[1].id,
                sort_order=2,
            ),
            BridgeDamageScalePath(
                bridge_type_id=bridge_types[0].id,
                part_id=parts[1].id,
                structure_type_id=structure_types[2].id,
                component_type_id=component_types[2].id,
                damage_type_id=damage_types[1].id,
                scale_id=scales[2].id,
                sort_order=3,
            ),
        ]

        for path in paths:
            session.add(path)
        session.commit()

        print("演示数据初始化完成！")
        print("================================")
        print("📊 数据统计:")
        print(f"  - 桥类型: {len(bridge_types)}个 (梁式桥、拱式桥)")
        print(f"  - 部位: {len(parts)}个 (上部结构、下部结构、桥面系、主拱圈)")
        print(f"  - 结构类型: {len(structure_types)}个")
        print(f"  - 部件类型: {len(component_types)}个")
        print(f"  - 病害类型: {len(damage_types)}个 (裂缝、腐蚀、沉降)")
        print(f"  - 标度: {len(scales)}个 (1-5级)")
        print(f"  - 完整路径: {len(paths)}个")
        print("================================")
        print("🎯 核心场景验证:")
        print("  ✅ 梁式桥 → 上部结构 → 钢结构A → 主梁A → 裂缝 → 标度1-3")
        print("  ✅ 梁式桥 → 上部结构 → 钢结构B → 主梁B → 裂缝 → 标度1-4")
        print("  ✅ 拱式桥 → 主拱圈 → 拱结构C → 拱圈C → 裂缝 → 标度1-5")
        print("================================")


if __name__ == "__main__":
    create_db_and_tables()
    init_demo_data()
