from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import traceback
import logging

from exceptions import (
    BaseException,
    NotFoundException,
    DuplicateException,
    ValidationException,
)
from utils.responses import api_response

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    全局异常处理中间件
    """

    async def dispatch(self, request: Request, call_next):
        """处理请求并捕获异常"""
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            logger.error(f"Exception occurred: {str(exc)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._handle_exception(exc)

    def _handle_exception(self, exc: Exception) -> Response:
        """
        根据异常类型返回相应的错误响应
        Args:
            exc: 异常实例
        Returns:
            统一格式的错误响应
        """

        # 业务异常处理
        if isinstance(exc, NotFoundException):  # 资源未找到
            return api_response(404, exc.message)

        if isinstance(exc, DuplicateException):  # 重复资源
            return api_response(400, exc.message)

        if isinstance(exc, ValidationException):  # 验证异常
            return api_response(400, exc.message)

        if isinstance(exc, BaseException):  # 自定义异常
            return api_response(400, exc.message)

        # HTTP异常
        if isinstance(exc, HTTPException):
            return api_response(exc.status_code, exc.detail)

        # Pydantic验证异常
        if isinstance(exc, RequestValidationError):
            error_messages = []
            for error in exc.errors():
                field = " -> ".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                error_messages.append(f"{field}: {message}")

            return api_response(400, f"参数验证失败: {'; '.join(error_messages)}")

        # 数据库完整性约束异常
        if isinstance(exc, IntegrityError):
            # 解析常见的数据库约束错误
            error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)

            if (
                "UNIQUE constraint failed" in error_msg
                or "Duplicate entry" in error_msg
            ):
                return api_response(400, "数据重复，请检查唯一性约束")
            elif "FOREIGN KEY constraint failed" in error_msg:
                return api_response(400, "外键约束错误，相关数据不存在")
            else:
                return api_response(400, "数据库约束错误")

        # 未知异常
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
        return api_response(500, "服务器内部错误")


def set_exception_handlers(app):
    """
    设置异常处理器
    """

    @app.exception_handler(BaseException)
    async def Base_exception_handler(request: Request, exc: BaseException):
        """异常处理器"""
        logger.warning(f"Base exception: {exc.message}")

        if isinstance(exc, NotFoundException):  # 资源未找到
            return api_response(404, exc.message)
        elif isinstance(exc, DuplicateException):  # 重复资源
            return api_response(400, exc.message)
        elif isinstance(exc, ValidationException):  # 验证异常
            return api_response(400, exc.message)
        else:
            return api_response(400, exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理器"""
        return api_response(exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """请求验证异常处理器"""
        error_messages = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")

        return api_response(400, f"参数验证失败: {'; '.join(error_messages)}")

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理器"""
        logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return api_response(500, "服务器内部错误")
