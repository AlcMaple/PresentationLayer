import logging
import traceback
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from exceptions import (
    BaseException,
    ExceptionType,
    NotFoundException,
    DuplicateException,
    ValidationException,
    SystemException,
)
from utils.responses import api_response


logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI):
    """异常处理器"""

    @app.exception_handler(BaseException)
    async def custom_base_exception_handler(request: Request, exc: BaseException):
        """
        处理所有继承自 BaseException 的自定义异常
        """
        # 系统异常
        if exc.exception_type == ExceptionType.SYSTEM:
            # 后端记录详细日志
            error_details = (
                f"System exception occurred: {exc.message} | Request: {request.url}"
            )
            if hasattr(exc, "original_error") and exc.original_error:
                error_details += f" | Original Error: {type(exc.original_error).__name__}: {exc.original_error}"
            logger.error(error_details)
            logger.error(f"Traceback: {traceback.format_exc()}")

            # 前端返回通用错误信息
            return api_response(500, "服务器内部错误")

        else:
            # 根据不同的业务异常类型，返回不同的状态码
            if isinstance(exc, NotFoundException):
                status_code = 404
            elif isinstance(exc, DuplicateException):
                status_code = 409
            elif isinstance(exc, ValidationException):
                status_code = 400
            else:  # 其他业务异常默认为 400
                status_code = 400

            logger.warning(
                f"Business exception: {exc.message} | Request: {request.url}"
            )
            return api_response(status_code, exc.message)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理 FastAPI/Starlette 抛出的 HTTP 异常"""
        return api_response(exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def pydantic_validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """处理 Pydantic 模型验证失败的异常"""
        error_messages = [
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in exc.errors()
        ]
        full_message = f"参数验证失败: {'; '.join(error_messages)}"
        logger.warning(
            f"Pydantic validation failed: {full_message} for request: {request.url}"
        )
        return api_response(400, full_message)

    @app.exception_handler(IntegrityError)
    async def sqlalchemy_integrity_handler(request: Request, exc: IntegrityError):
        """处理 SQLAlchemy 数据库完整性异常，通常视为业务逻辑错误"""
        error_msg = str(exc.orig).lower() if hasattr(exc, "orig") else str(exc).lower()

        # 业务错误信息
        if "unique constraint" in error_msg or "duplicate entry" in error_msg:
            message = "数据已存在，请勿重复添加"
        elif "foreign key constraint" in error_msg:
            message = "关联资源不存在，请检查提交的数据"
        else:
            message = "数据库操作失败，请检查数据完整性"

        logger.error(
            f"Database Integrity Error: {message} | Details: {exc.orig} | Request: {request.url}"
        )
        return api_response(400, message)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        其他异常
        """
        logger.error(
            f"Unhandled internal server error: {type(exc).__name__}: {exc} for request: {request.url}"
        )
        logger.error(f"Traceback: {traceback.format_exc()}")
        return api_response(500, "服务器内部错误")
