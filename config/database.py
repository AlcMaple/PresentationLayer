from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

from .settings import settings
from models import (
    Categories,
    BridgeTypes,
    BridgeParts,
    BridgeStructures,
    BridgeComponentTypes,
    BridgeComponentForms,
    BridgeDiseases,
    BridgeScales,
    BridgeQualities,
    BridgeQuantities,
    Paths,
    AssessmentUnit,
)

# 数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # echo=settings.ENVIRONMENT == "development",  # 输出SQL日志
    echo=False,  # 输出SQL日志
    pool_recycle=3600,
)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    """
    with Session(engine) as session:
        yield session


def create_tables():
    """
    创建数据表
    """
    # print("创建数据表...")
    try:
        SQLModel.metadata.create_all(engine)
        # print("数据表创建成功")

        # print("已创建的表：")
        # for table_name in SQLModel.metadata.tables.keys():
        #     print(f"   - {table_name}")
    except Exception as e:
        print(f"数据表创建失败：{e}")
        raise


def drop_tables():
    """删除所有数据表"""
    print("删除所有数据表...")
    SQLModel.metadata.drop_all(engine)
    print("数据表删除完成")
