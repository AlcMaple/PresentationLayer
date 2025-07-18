from typing import Dict, List, Tuple
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from middleware import ExceptionHandlerMiddleware, set_exception_handlers


class AppFactory:
    """应用工厂类"""

    def __init__(self):
        self.modules = {}

    def register_module(self, name: str, router, description: str):
        """注册模块"""
        self.modules[name] = {"router": router, "description": description}

    def create_module_app(self, module_name: str) -> FastAPI:
        """创建单个模块应用"""
        if module_name not in self.modules:
            raise ValueError(f"模块 '{module_name}' 未注册")

        module = self.modules[module_name]

        app = FastAPI(
            title=f"{settings.PROJECT_NAME} - {module['description']}模块",
            version=settings.VERSION,
            description=f"{settings.PROJECT_NAME}{module['description']}API",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # 包含模块路由
        app.include_router(module["router"], prefix="/api")
        return app

    def create_main_app(self) -> FastAPI:
        """创建主应用"""
        app = FastAPI(
            title=settings.PROJECT_NAME,
            version=settings.VERSION,
            description=f"{settings.PROJECT_NAME}API",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # CORS配置
        self._setup_cors(app)

        # 异常处理
        self._setup_exception_handling(app)

        # 包含所有模块路由
        for module in self.modules.values():
            app.include_router(module["router"], prefix="/api")

        return app

    def create_all_apps(self) -> Tuple[FastAPI, Dict[str, FastAPI]]:
        """创建主应用和所有模块应用"""
        main_app = self.create_main_app()
        module_apps = {}

        for module_name in self.modules.keys():
            module_apps[module_name] = self.create_module_app(module_name)

        return main_app, module_apps

    def mount_module_apps(self, main_app: FastAPI, module_apps: Dict[str, FastAPI]):
        """将模块应用挂载到主应用"""
        for module_name, module_app in module_apps.items():
            main_app.mount(f"/{module_name}", module_app)

    def _setup_cors(self, app: FastAPI):
        """配置CORS"""
        if settings.is_development:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        else:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["GET", "POST", "PUT", "DELETE"],
                allow_headers=["*"],
            )

    def _setup_exception_handling(self, app: FastAPI):
        """配置异常处理"""
        app.add_middleware(ExceptionHandlerMiddleware)
        set_exception_handlers(app)


# 工厂实例
app_factory = AppFactory()


def get_app_factory() -> AppFactory:
    """获取应用工厂实例"""
    return app_factory
