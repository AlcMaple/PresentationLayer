from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.settings import settings
from api.router import router
from lifecycle import setup_lifespan
from middleware import ExceptionHandlerMiddleware, set_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="桥梁健康监控系统后端API",
    )

    # CORS配置
    if settings.is_development:
        # 开发环境
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # 生产环境
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 后续改为前端域名
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )

    # 异常处理中间件
    app.add_middleware(ExceptionHandlerMiddleware)

    # 异常处理器
    set_exception_handlers(app)

    # API路由
    app.include_router(router, prefix="/api")

    return app


app = create_app()

# 设置应用生命周期
setup_lifespan(app)

if __name__ == "__main__":
    if settings.is_development:
        # 开发环境
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            workers=1,
        )
    else:
        # 生产环境
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.PORT,
            workers=4,
        )
