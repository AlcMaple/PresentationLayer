import uvicorn

from config.settings import settings
from api.router import router, router_paths
from lifecycle import setup_lifespan
from app_factory import get_app_factory


def setup_applications():
    """设置应用配置"""
    factory = get_app_factory()

    # 注册模块
    factory.register_module("base", router, "基础管理")
    factory.register_module("paths", router_paths, "路径管理")

    # 创建所有应用
    main_app, module_apps = factory.create_all_apps()

    # 挂载模块应用
    factory.mount_module_apps(main_app, module_apps)

    return main_app


# 创建应用实例
app = setup_applications()

# 设置应用生命周期
setup_lifespan(app)

if __name__ == "__main__":
    if settings.is_development:
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            workers=1,
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.PORT,
            workers=4,
        )
