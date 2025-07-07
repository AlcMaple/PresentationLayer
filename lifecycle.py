from contextlib import asynccontextmanager
from fastapi import FastAPI

from config.settings import settings
from config.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"应用启动 - 环境: {settings.ENVIRONMENT}")
    print(f"数据库: {settings.MYSQL_DATABASE}")

    # 创建数据表
    create_tables()
    print("数据表创建完成")

    yield

    # 关闭时执行
    print("应用正在关闭...")


def setup_lifespan(app: FastAPI):
    """为应用设置生命周期"""
    app.router.lifespan_context = lifespan
