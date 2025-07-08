import sys
import os
from sqlmodel import Session, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine


def clear_all_tables():
    """清空所有基础表数据"""
    tables = [
        "bridge_quantities",
        "bridge_qualities",
        "bridge_scales",
        "bridge_hazards",
        "bridge_component_forms",
        "bridge_component_types",
        "bridge_structures",
        "bridge_parts",
        "bridge_types",
    ]

    with Session(engine) as session:
        for table in tables:
            session.execute(text(f"DELETE FROM {table}"))
            session.execute(text(f"ALTER TABLE {table} AUTO_INCREMENT = 1"))
        session.commit()
        print("所有表数据已清空")


if __name__ == "__main__":
    clear_all_tables()
